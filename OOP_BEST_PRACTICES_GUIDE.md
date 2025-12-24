# 🎯 OOP Best Practices - Interview Guide

## Complete Implementation of Object-Oriented Design Principles

This guide demonstrates production-grade OOP patterns commonly asked in technical interviews.

---

## 📚 Table of Contents

1. [SOLID Principles](#solid-principles)
2. [Design Patterns](#design-patterns)
3. [Domain-Driven Design](#domain-driven-design)
4. [Clean Architecture](#clean-architecture)
5. [Interview Questions & Answers](#interview-questions)

---

## SOLID Principles

### 1. Single Responsibility Principle (SRP)

**Definition:** A class should have only one reason to change.

**Implementation:**
```python
# ❌ BAD: Multiple responsibilities
class Sensor:
    def read_data(self): pass
    def save_to_database(self): pass
    def send_alert(self): pass
    def generate_report(self): pass

# ✅ GOOD: Single responsibility
class Sensor:
    def read_data(self): pass

class SensorRepository:
    def save(self, sensor): pass

class AlertService:
    def send_alert(self, sensor): pass

class ReportGenerator:
    def generate(self, sensor): pass
```

**In Our Project:**
- `Sensor` entity: Only manages sensor state
- `SensorRepository`: Only handles data persistence
- `SensorService`: Only contains business logic
- `AlertObserver`: Only handles alerts

### 2. Open/Closed Principle (OCP)

**Definition:** Open for extension, closed for modification.

**Implementation:**
```python
# File: app/domain/entities.py

class SensorValidator(ABC):
    @abstractmethod
    def validate(self, reading: SensorReading) -> bool:
        pass

# Extend without modifying base
class TemperatureValidator(SensorValidator):
    def validate(self, reading: SensorReading) -> bool:
        return -40 <= reading.temperature <= 85

class HumidityValidator(SensorValidator):
    def validate(self, reading: SensorReading) -> bool:
        return 0 <= reading.humidity <= 100
```

**Interview Question:** "How do you add new validation without changing existing code?"
**Answer:** Use abstract base classes and inheritance to extend functionality.

### 3. Liskov Substitution Principle (LSP)

**Definition:** Subtypes must be substitutable for their base types.

**Implementation:**
```python
# All validators can be used interchangeably
def validate_reading(validator: SensorValidator, reading: SensorReading):
    return validator.validate(reading)

# Works with any validator
temp_validator = TemperatureValidator()
humidity_validator = HumidityValidator()

validate_reading(temp_validator, reading)  # ✅
validate_reading(humidity_validator, reading)  # ✅
```

### 4. Interface Segregation Principle (ISP)

**Definition:** Clients shouldn't depend on interfaces they don't use.

**Implementation:**
```python
# File: app/domain/repositories.py

# ❌ BAD: Fat interface
class IRepository(ABC):
    def get_by_id(self): pass
    def get_all(self): pass
    def save(self): pass
    def delete(self): pass
    def get_statistics(self): pass  # Not all repos need this
    def export_to_csv(self): pass   # Not all repos need this

# ✅ GOOD: Segregated interfaces
class IReadRepository(ABC):
    def get_by_id(self): pass
    def get_all(self): pass

class IWriteRepository(ABC):
    def save(self): pass
    def delete(self): pass

class IStatisticsRepository(ABC):
    def get_statistics(self): pass
```

### 5. Dependency Inversion Principle (DIP)

**Definition:** Depend on abstractions, not concretions.

**Implementation:**
```python
# File: app/services/sensor_service.py

class SensorService:
    def __init__(
        self,
        sensor_repo: ISensorRepository,  # ✅ Depend on interface
        reading_repo: ISensorReadingRepository
    ):
        self._sensor_repo = sensor_repo
        self._reading_repo = reading_repo

# Can inject any implementation
service = SensorService(
    InMemorySensorRepository(),  # For testing
    # OR
    PostgreSQLSensorRepository()  # For production
)
```

**Interview Question:** "Why use dependency injection?"
**Answer:** 
- Testability (mock dependencies)
- Flexibility (swap implementations)
- Loose coupling
- Easier maintenance

---

## Design Patterns

### 1. Factory Pattern

**When to use:** Complex object creation, multiple variants

**File:** `app/patterns/factory.py`

```python
# Create sensors without knowing implementation details
sensor = SensorFactory.create_temperature_sensor("TEMP_001", location)
```

**Interview Question:** "Factory vs Constructor?"
**Answer:**
- Factory: Complex creation logic, multiple variants
- Constructor: Simple, direct instantiation

### 2. Builder Pattern

**When to use:** Objects with many optional parameters

**File:** `app/patterns/factory.py`

```python
# Fluent interface for complex object
reading = (SensorReadingBuilder("TEMP_001")
           .with_temperature(22.5)
           .with_humidity(45.0)
           .with_battery_level(85.0)
           .build())
```

**Interview Question:** "Builder vs Constructor with many parameters?"
**Answer:**
- Builder: Optional parameters, fluent API, validation
- Constructor: Required parameters, simple creation

### 3. Repository Pattern

**When to use:** Abstract data access layer

**File:** `app/domain/repositories.py`

```python
# Business logic doesn't know about database
sensor = await sensor_repo.get_by_id("TEMP_001")
```

**Interview Question:** "Why use Repository?"
**Answer:**
- Separation of concerns
- Testability (mock data layer)
- Database independence
- Centralized data access logic

### 4. Observer Pattern

**When to use:** Event-driven architecture, notifications

**File:** `app/patterns/observer.py`

```python
# Multiple observers react to events
subject.attach(AlertObserver())
subject.attach(LoggingObserver())
subject.attach(MetricsObserver())

await subject.notify_reading(reading)  # All observers notified
```

**Interview Question:** "Observer vs Callback?"
**Answer:**
- Observer: Multiple subscribers, loose coupling
- Callback: Single handler, tight coupling

### 5. Strategy Pattern

**When to use:** Interchangeable algorithms

**File:** `app/domain/entities.py`

```python
# Different validation strategies
validator = CompositeValidator([
    TemperatureValidator(),
    HumidityValidator()
])
```

**Interview Question:** "Strategy vs If-Else?"
**Answer:**
- Strategy: Open/Closed, testable, extensible
- If-Else: Violates OCP, hard to test

---

## Domain-Driven Design (DDD)

### Entities vs Value Objects

**Entity:** Has identity, mutable
```python
@dataclass
class Sensor:  # Entity
    sensor_id: str  # Identity
    status: SensorStatus  # Can change
```

**Value Object:** No identity, immutable
```python
@dataclass(frozen=True)
class Location:  # Value Object
    building: str
    floor: int
    room: str
```

**Interview Question:** "When to use Entity vs Value Object?"
**Answer:**
- Entity: Needs tracking over time (User, Order, Sensor)
- Value Object: Describes something (Address, Money, Location)

### Aggregates

**Definition:** Cluster of entities treated as a unit

```python
class Sensor:  # Aggregate Root
    readings: List[SensorReading]  # Part of aggregate
    
    def add_reading(self, reading):
        # Enforce business rules
        if reading.sensor_id != self.sensor_id:
            raise ValueError("Invalid reading")
        self.readings.append(reading)
```

**Interview Question:** "Why use Aggregates?"
**Answer:**
- Consistency boundary
- Transaction boundary
- Encapsulation of business rules

---

## Clean Architecture Layers

```
┌─────────────────────────────────────┐
│     Presentation Layer              │
│  (FastAPI Controllers/Routers)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Application Layer               │
│  (Services, Use Cases)              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Domain Layer                    │
│  (Entities, Value Objects)          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Infrastructure Layer            │
│  (Repositories, Database)           │
└─────────────────────────────────────┘
```

### Layer Responsibilities

1. **Domain Layer** (`app/domain/`)
   - Business entities
   - Business rules
   - No dependencies on other layers

2. **Application Layer** (`app/services/`)
   - Use cases
   - Business logic orchestration
   - Depends only on domain

3. **Infrastructure Layer** (`app/repositories/`)
   - Database access
   - External services
   - Implements domain interfaces

4. **Presentation Layer** (`app/routers/`)
   - HTTP endpoints
   - Request/response handling
   - Depends on application layer

---

## Interview Questions & Answers

### Q1: "Explain the difference between composition and inheritance"

**Answer:**
```python
# Inheritance (IS-A relationship)
class TemperatureSensor(Sensor):
    pass

# Composition (HAS-A relationship)
class Sensor:
    def __init__(self, validator: SensorValidator):
        self.validator = validator  # Has a validator
```

**When to use:**
- Inheritance: True IS-A relationship, shared behavior
- Composition: Flexibility, avoid deep hierarchies

### Q2: "How do you ensure thread safety in your classes?"

**Answer:**
```python
from threading import Lock

class ThreadSafeSensorRepository:
    def __init__(self):
        self._sensors = {}
        self._lock = Lock()
    
    def save(self, sensor):
        with self._lock:
            self._sensors[sensor.sensor_id] = sensor
```

### Q3: "Explain encapsulation with an example"

**Answer:**
```python
class Sensor:
    def __init__(self):
        self._readings = []  # Private
    
    def add_reading(self, reading):
        # Validation before adding
        if self._validate(reading):
            self._readings.append(reading)
    
    def get_readings(self):
        # Return copy, not internal list
        return self._readings.copy()
```

### Q4: "What is polymorphism? Give an example"

**Answer:**
```python
def process_validator(validator: SensorValidator):
    # Works with any validator type
    return validator.validate(reading)

# Polymorphic behavior
process_validator(TemperatureValidator())
process_validator(HumidityValidator())
process_validator(CompositeValidator([...]))
```

### Q5: "How do you handle errors in OOP?"

**Answer:**
```python
class SensorError(Exception):
    """Base exception for sensor errors"""
    pass

class SensorNotFoundError(SensorError):
    """Specific error type"""
    pass

class InvalidReadingError(SensorError):
    """Another specific error"""
    pass

# Usage
try:
    sensor = await repo.get_by_id("TEMP_001")
    if not sensor:
        raise SensorNotFoundError("Sensor not found")
except SensorNotFoundError as e:
    # Handle specific error
    logger.error(f"Sensor error: {e}")
```

### Q6: "Explain dependency injection benefits"

**Answer:**
1. **Testability:** Mock dependencies
2. **Flexibility:** Swap implementations
3. **Loose Coupling:** Classes don't create dependencies
4. **Configuration:** External configuration of dependencies

```python
# Without DI (tight coupling)
class SensorService:
    def __init__(self):
        self.repo = PostgreSQLRepository()  # ❌ Hard-coded

# With DI (loose coupling)
class SensorService:
    def __init__(self, repo: ISensorRepository):
        self.repo = repo  # ✅ Injected

# Easy to test
service = SensorService(MockRepository())
```

### Q7: "What is the difference between abstract class and interface?"

**Answer:**
```python
# Abstract class (can have implementation)
class SensorBase(ABC):
    def __init__(self):
        self.status = "active"
    
    @abstractmethod
    def read_data(self):
        pass
    
    def get_status(self):  # Concrete method
        return self.status

# Interface (only contracts)
class ISensorRepository(ABC):
    @abstractmethod
    def save(self, sensor): pass
    
    @abstractmethod
    def get_by_id(self, id): pass
```

**When to use:**
- Abstract class: Shared implementation, IS-A relationship
- Interface: Contract only, multiple inheritance

---

## Running the Examples

### 1. Test Domain Entities
```bash
cd sensor-backend
python -m app.domain.entities
```

### 2. Test Factory Pattern
```bash
python -m app.patterns.factory
```

### 3. Test Observer Pattern
```bash
python -m app.patterns.observer
```

### 4. Run Complete Service
```bash
python app/secure_app.py
```

---

## Code Quality Checklist

✅ **SOLID Principles**
- [ ] Single Responsibility
- [ ] Open/Closed
- [ ] Liskov Substitution
- [ ] Interface Segregation
- [ ] Dependency Inversion

✅ **Design Patterns**
- [ ] Factory for object creation
- [ ] Builder for complex objects
- [ ] Repository for data access
- [ ] Observer for events
- [ ] Strategy for algorithms

✅ **Clean Code**
- [ ] Meaningful names
- [ ] Small functions
- [ ] No code duplication
- [ ] Proper error handling
- [ ] Comprehensive tests

✅ **Architecture**
- [ ] Layered architecture
- [ ] Separation of concerns
- [ ] Dependency injection
- [ ] Domain-driven design

---

## Resources

- **Books:**
  - "Clean Code" by Robert C. Martin
  - "Design Patterns" by Gang of Four
  - "Domain-Driven Design" by Eric Evans

- **Online:**
  - [Refactoring Guru - Design Patterns](https://refactoring.guru/design-patterns)
  - [SOLID Principles](https://www.digitalocean.com/community/conceptual_articles/s-o-l-i-d-the-first-five-principles-of-object-oriented-design)

---

## Summary

This project demonstrates:
1. ✅ All SOLID principles
2. ✅ 5+ design patterns
3. ✅ Domain-driven design
4. ✅ Clean architecture
5. ✅ Production-ready code
6. ✅ Comprehensive documentation

**Perfect for technical interviews!** 🎯
