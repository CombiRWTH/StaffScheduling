import {createModule} from '@evyweb/ioctopus';
import {DI_SYMBOLS} from '@/di/types';
import {LowdbEmployeeRepository} from '@/infrastructure/repositories/lowdb-employee.repository';
import {makeGetAllEmployeesUseCase} from '@/application/use-cases/employees/get-all-employees.use-case';
import {makeGetEmployeeUseCase} from '@/application/use-cases/employees/get-employee.use-case';
import {makeCreateEmployeeUseCase} from '@/application/use-cases/employees/create-employee.use-case';
import {makeGetAllEmployeesController} from '@/controllers/employees/get-all-employees.controller';
import {makeGetEmployeeController} from '@/controllers/employees/get-employee.controller';
import {makeCreateEmployeeController} from '@/controllers/employees/create-employee.controller';

export function createEmployeesModule() {
    const m = createModule();

    m.bind(DI_SYMBOLS.IEmployeeRepository).toClass(LowdbEmployeeRepository, [], 'singleton');

    m.bind(DI_SYMBOLS.IGetAllEmployeesUseCase).toHigherOrderFunction(makeGetAllEmployeesUseCase, [DI_SYMBOLS.IEmployeeRepository]);
    m.bind(DI_SYMBOLS.IGetEmployeeUseCase).toHigherOrderFunction(makeGetEmployeeUseCase, [DI_SYMBOLS.IEmployeeRepository]);
    m.bind(DI_SYMBOLS.ICreateEmployeeUseCase).toHigherOrderFunction(makeCreateEmployeeUseCase, [DI_SYMBOLS.IEmployeeRepository]);

    m.bind(DI_SYMBOLS.IGetAllEmployeesController).toHigherOrderFunction(makeGetAllEmployeesController, [DI_SYMBOLS.IGetAllEmployeesUseCase]);
    m.bind(DI_SYMBOLS.IGetEmployeeController).toHigherOrderFunction(makeGetEmployeeController, [DI_SYMBOLS.IGetEmployeeUseCase]);
    m.bind(DI_SYMBOLS.ICreateEmployeeController).toHigherOrderFunction(makeCreateEmployeeController, [DI_SYMBOLS.ICreateEmployeeUseCase]);

    return m;
}
