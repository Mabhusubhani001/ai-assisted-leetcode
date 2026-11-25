export interface TestCasePublic {
  id: string;
  stdin: string;
  expected_stdout: string;
}

export interface QuestionDetail {
  id: string;
  title: string;
  slug: string;
  difficulty: "Easy" | "Medium" | "Hard" | string;
  description: string;
  starter_code: Record<string, string>;
  memory_limit_mb: number;
  time_limit_sec: number;
  test_cases: TestCasePublic[];
}

export interface ChatEvaluation {
  is_approved: boolean;
  feedback: string;
  detected_data_structure?: string | null;
  detected_algorithm?: string | null;
  time_complexity?: string | null;
  space_complexity?: string | null;
  missing_requirements: string[];
  starter_code?: string | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  turn_tokens?: number;
  tokens_consumed: number;
  tokens_used: number;
  token_limit: number;
  is_locked: boolean;
  provider_used?: string;
  model_used?: string;
}

export interface SubmissionResponse {
  id: string;
  user_id: string;
  question_id: string;
  language_id: number;
  source_code: string;
  status: "PENDING" | "RUNNING" | "ACCEPTED" | "WRONG_ANSWER" | "TIME_LIMIT_EXCEEDED" | "MEMORY_LIMIT_EXCEEDED" | "RUNTIME_ERROR" | "COMPILATION_ERROR";
  execution_time_sec?: number | null;
  memory_used_kb?: number | null;
  compile_output?: string | null;
  stderr?: string | null;
  passed_test_cases: number;
  total_test_cases: number;
  failed_test_case_info?: {
    test_case_number?: number;
    stdin?: string;
    expected_stdout?: string;
    actual_stdout?: string;
    is_hidden?: boolean;
    message?: string;
  } | null;
  created_at: string;
}
