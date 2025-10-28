export interface PaginationQuery {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface NumericFilterOperator {
  gt?: number;  // greater than
  gte?: number; // greater than or equal
  lt?: number;  // less than
  lte?: number; // less than or equal
  eq?: number;  // equal
  ne?: number;  // not equal
}

export interface DateFilterOperator {
  gt?: string;  // greater than
  gte?: string; // greater than or equal
  lt?: string;  // less than
  lte?: string; // less than or equal
}

export interface PaginationMetadata {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMetadata;
}

export interface SingleResponse<T> {
  success: boolean;
  data: T;
}

export interface ErrorResponse {
  success: boolean;
  message: string;
  error?: string;
}
