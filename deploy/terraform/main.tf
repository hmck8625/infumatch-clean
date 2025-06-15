# =============================================================================
# Terraform メインコンフィグレーション
# =============================================================================
# Google Cloud インフラストラクチャのコード化

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Terraform State の管理（Cloud Storage）
  backend "gcs" {
    bucket = "hackathon-462905-terraform-state"
    prefix = "infumatch"
  }
}

# プロバイダー設定
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ローカル変数
locals {
  services = [
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "scheduler.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ]
}

# =============================================================================
# Google Cloud APIs の有効化
# =============================================================================
resource "google_project_service" "apis" {
  for_each = toset(local.services)
  
  project = var.project_id
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# =============================================================================
# Artifact Registry
# =============================================================================
resource "google_artifact_registry_repository" "infumatch" {
  provider = google-beta
  
  location      = var.region
  repository_id = "infumatch"
  description   = "InfuMatch application Docker images"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Secret Manager
# =============================================================================
resource "google_secret_manager_secret" "youtube_api_key" {
  secret_id = "youtube-api-key"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "youtube_api_key" {
  secret      = google_secret_manager_secret.youtube_api_key.id
  secret_data = var.youtube_api_key
}

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# =============================================================================
# Firestore Database
# =============================================================================
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Cloud Storage
# =============================================================================
resource "google_storage_bucket" "terraform_state" {
  name     = "${var.project_id}-terraform-state"
  location = var.region
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "backup" {
  name     = "${var.project_id}-backup"
  location = var.region
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Pub/Sub Topics
# =============================================================================
resource "google_pubsub_topic" "youtube_collection_trigger" {
  name = "youtube-collection-trigger"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "ai_analysis_trigger" {
  name = "ai-analysis-trigger"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "data_maintenance_trigger" {
  name = "data-maintenance-trigger"

  depends_on = [google_project_service.apis]
}

# =============================================================================
# IAM サービスアカウント
# =============================================================================
resource "google_service_account" "app_engine_default" {
  account_id   = "app-engine-default"
  display_name = "InfuMatch Application Service Account"
  description  = "Service account for InfuMatch application components"
}

# Cloud Run サービスアカウントの権限
resource "google_project_iam_member" "app_engine_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.app_engine_default.email}"
}

resource "google_project_iam_member" "app_engine_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app_engine_default.email}"
}

resource "google_project_iam_member" "app_engine_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_engine_default.email}"
}

resource "google_project_iam_member" "app_engine_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.writer"
  member  = "serviceAccount:${google_service_account.app_engine_default.email}"
}

resource "google_project_iam_member" "app_engine_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.app_engine_default.email}"
}

# =============================================================================
# Cloud Scheduler Jobs
# =============================================================================
resource "google_cloud_scheduler_job" "youtube_collection" {
  name             = "youtube-influencer-collection"
  description      = "YouTube インフルエンサーデータの定期収集"
  schedule         = "0 */6 * * *"
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "600s"

  retry_config {
    retry_count = 3
  }

  pubsub_target {
    topic_name = google_pubsub_topic.youtube_collection_trigger.id
    data       = base64encode(jsonencode({
      source = "cloud-scheduler"
      job    = "youtube_collection"
    }))
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "ai_analysis" {
  name             = "ai-influencer-analysis"
  description      = "インフルエンサーのAI分析処理"
  schedule         = "0 2 * * *"
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "1800s"

  retry_config {
    retry_count = 2
  }

  pubsub_target {
    topic_name = google_pubsub_topic.ai_analysis_trigger.id
    data       = base64encode(jsonencode({
      source = "cloud-scheduler"
      job    = "ai_analysis"
    }))
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "data_maintenance" {
  name             = "data-maintenance"
  description      = "データクリーンアップとレポート生成"
  schedule         = "0 1 * * 0"
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "3600s"

  retry_config {
    retry_count = 1
  }

  pubsub_target {
    topic_name = google_pubsub_topic.data_maintenance_trigger.id
    data       = base64encode(jsonencode({
      source = "cloud-scheduler"
      job    = "data_maintenance"
    }))
  }

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Monitoring & Alerting
# =============================================================================
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  
  labels = {
    email_address = var.notification_email
  }
}

resource "google_monitoring_alert_policy" "cloud_run_error_rate" {
  display_name = "Cloud Run High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run error rate"
    
    condition_threshold {
      filter         = "resource.type=\"cloud_run_revision\""
      duration       = "300s"
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  depends_on = [google_project_service.apis]
}

# =============================================================================
# 出力値
# =============================================================================
output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud Region"
  value       = var.region
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = google_artifact_registry_repository.infumatch.name
}

output "firestore_database" {
  description = "Firestore Database Name"
  value       = google_firestore_database.database.name
}

output "scheduler_jobs" {
  description = "Cloud Scheduler Job Names"
  value = [
    google_cloud_scheduler_job.youtube_collection.name,
    google_cloud_scheduler_job.ai_analysis.name,
    google_cloud_scheduler_job.data_maintenance.name
  ]
}

output "pubsub_topics" {
  description = "Pub/Sub Topic Names"
  value = [
    google_pubsub_topic.youtube_collection_trigger.name,
    google_pubsub_topic.ai_analysis_trigger.name,
    google_pubsub_topic.data_maintenance_trigger.name
  ]
}