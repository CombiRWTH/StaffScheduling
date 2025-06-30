Efficient staff scheduling in hospitals is crucial for the optimal allocation of personnel resources and for ensuring that workflows run smoothly. This, in turn, directly affects the quality of patient care. Currently, duty rosters are often created manually, which is time-consuming and prone to inefficiencies. This complexity arises from the need to consider multiple constraints, such as staffing ratios and labor laws (e.g., working time regulations).

## Goal
> Our objective is to streamline the creation of staff schedules by automating the process. This involves assigning five different types of shifts ('Early', 'Late', 'Night', 'Intermediate' and 'Special') across employees. Our solution aims to meet all specified conditions, ensuring that the resulting schedule is ready for implementation or requires only minor adjustments by trained personnel.

This goal was established in collaboration with Pradtke GmbH and St. Marien-Hospital Düren, who provided the necessary domain expertise.

## Workflow
To achieve this goal, we need to complete four key steps:

1. Provide additional information, such as employee preferences, in a JSON file.
2. Connect to TimeOffice (Schedule Planner) to retrieve employee and scheduling data.
3. Approximate the optimal schedule by assigning shifts to employees.
4. Write the final solution back into TimeOffice.


## Conditions
The requirements that our code must fulfill were defined by our expert partners. These conditions are designed to comply with German labor laws, adhere to shift work recommendations, and reflect the actual workflows in the hospital setting.

We differentiate between two types of conditions: constraints (hard) and objectives (soft).

- **Constraints** are essential requirements that the schedule must meet. For example, this includes factors like already planned vacation days.

- **Objectives**, on the other hand, represent aspects that can be optimized but do not constitute strict requirements. An example of this would be minimizing the number of consecutive night shifts.

A list of all the conditions can be found here: [**List of Conditions**](/user-view/list-of-conditions.md).

## Related Links
- [Mathematical / Technical Problem Formulation](/developer-view/mathematical-problem-formulation.md)
- [List of Conditions](/user-view(list-of-conditions.md))
