// ============ Global Type Definitions ============

/** Base DTO for all entities */
export interface BaseDto {
  id: string;
  created_at: string;
  updated_at: string;
}

/** API Error Response */
export interface ApiErrorResponse {
  status: number;
  message: string;
  code?: string;
  errors?: Record<string, string[]>;
}

/** API Success Response */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// ============ Common Enums ============

export enum HttpStatus {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  INTERNAL_SERVER_ERROR = 500,
}

// ============ HTTP Error Mapping ============
export const getErrorMessage = (status: number): string => {
  const messages: Record<number, string> = {
    [HttpStatus.BAD_REQUEST]: 'Invalid request data',
    [HttpStatus.UNAUTHORIZED]: 'Please login again',
    [HttpStatus.FORBIDDEN]: 'You do not have permission',
    [HttpStatus.NOT_FOUND]: 'Resource not found',
    [HttpStatus.CONFLICT]: 'This resource already exists',
    [HttpStatus.UNPROCESSABLE_ENTITY]: 'Validation failed',
    [HttpStatus.INTERNAL_SERVER_ERROR]: 'Server error, please try again',
  };
  return messages[status] || 'An error occurred';
};
