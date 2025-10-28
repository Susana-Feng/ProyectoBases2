export interface PaginationQuery {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
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
