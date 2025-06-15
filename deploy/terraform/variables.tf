# =============================================================================
# Terraform 変数定義
# =============================================================================

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "hackathon-462905"
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "asia-northeast1"
}

variable "youtube_api_key" {
  description = "YouTube Data API Key"
  type        = string
  sensitive   = true
  default     = "AIzaSyDApW6Csr_FEbGkOyxJESReh85I03NTjaw"
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
  default     = "AIzaSyCwEzSE-OPbznJb8OniNpf9zqTMIOAKbMk"
}

variable "notification_email" {
  description = "Email address for monitoring notifications"
  type        = string
  default     = "admin@infumatch.com"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "2Gi"
}