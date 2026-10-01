import { CaseUnit } from "@/entities/models/case.model";

export interface ICaseRepository {
  list(): Promise<CaseUnit[]>;
}
