# Introduction
This chapter provides step-by-step guides for extending the shift scheduling system with new components. The system is designed to be modular and extensible, allowing you to add custom logic for your specific scheduling requirements.

## Overview
The shift scheduling system has three main extensible components:

### Variables
**Decision elements** that the solver can set when creating a schedule. Variables represent choices like "Does employee X work shift Y on day Z?".

### Constraints
**Rules and requirements** that must be satisfied in any valid schedule. Constraints define what is allowed or forbidden, such as "An employee cannot work more than 8 hours per day".

### Objectives
**Goals to optimize** when multiple valid schedules exist. Objectives define what makes one schedule better than another, such as "Minimize overtime hours".

## When to Add Each Component
### **[Adding Variables](./how-to-add-variable.md)**

- You need to track new decision points in your scheduling problem
- You want to introduce new types of assignments or allocations
- You need intermediate calculations that other constraints or objectives will reference

### **[Adding Constraints](./how-to-add-constraint.md)**

- You have new business rules or requirements that must be enforced
- You need to ensure certain scheduling patterns are followed or avoided
- You want to add compliance requirements or safety regulations

### **[Adding Objectives](./how-to-add-objective.md)**

- You want to optimize for new criteria beyond existing goals
- You need to balance competing priorities in your scheduling decisions
- You want to improve specific aspects of schedule quality

For more information about the overall system architecture, see the [Codebase Overview](../codebase-overview.md).
