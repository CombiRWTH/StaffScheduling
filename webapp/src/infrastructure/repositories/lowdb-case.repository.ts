import { ICaseRepository } from "@/application/ports/case.repository";
import { CaseUnit } from "@/entities/models/case.model";
import { listCases } from "@/infrastructure/persistence/lowdb/case.db";

export class LowdbCaseRepository implements ICaseRepository {
  async list(): Promise<CaseUnit[]> {
    return listCases();
  }
}
