export interface Driver {
  id: number
  position: number
  driver_name: string
  team: string
  points: number
  wins?: number
}

export interface Constructor {
  id: number
  position: number
  team_name: string
  points: number
  wins?: number
}

export interface RaceResult {
  id: number
  position: number
  driver_name: string
  team: string
  time: string
  points: number
  status: string
}

export interface Race {
  id: number
  round: number
  race_name: string
  date: string
  country: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

// Periodic Tasks Types
export interface CrontabSchedule {
  id: number
  minute: string
  hour: string
  day_of_week: string
  day_of_month: string
  month_of_year: string
  timezone: string
  human_readable: string
}

export interface IntervalSchedule {
  id: number
  every: number
  period: 'days' | 'hours' | 'minutes' | 'seconds' | 'microseconds'
  human_readable: string
}

export interface PeriodicTask {
  id: number
  name: string
  task: string
  crontab?: CrontabSchedule
  interval?: IntervalSchedule
  crontab_id?: number
  interval_id?: number
  args: string
  kwargs: any
  queue: string | null
  exchange: string | null
  routing_key: string | null
  expires: string | null
  enabled: boolean
  last_run_at: string | null
  total_run_count: number
  date_changed: string
  description: string
  schedule_display: string
}

export interface CrontabExplanation {
  crontab: string
  explanation: string
}

// Data Audit Types
export interface DataAuditSuggestion {
  id: number
  table_name: string
  field_name: string
  record_id: number
  record_identifier: string
  current_value: string | null
  suggested_value: string
  confidence_score: number
  source_name: string
  source_url: string
  source_timestamp: string
  applied: boolean
  applied_at: string | null
  rejected: boolean
  rejection_reason: string
  created_at: string
}

export interface DataAuditReport {
  id: number
  execution_date: string
  status: 'pending' | 'completed' | 'failed'
  execution_time_seconds: number | null
  total_tables_scanned: number
  total_fields_scanned: number
  total_empty_fields_found: number
  total_suggestions_found: number
  audit_results: any
  error_message: string
  suggestions: DataAuditSuggestion[]
  suggestions_count: {
    total: number
    pending: number
    applied: number
    rejected: number
  }
}

export interface SuggestionsByTable {
  table_name: string
  total: number
  pending: number
  applied: number
  rejected: number
}

export interface BulkApplyResult {
  message: string
  results: {
    success: Array<{
      id: number
      table: string
      field: string
    }>
    failed: Array<{
      id: number
      table: string
      field: string
      error: string
    }>
  }
}

export interface BulkRejectResult {
  message: string
  count: number
}
