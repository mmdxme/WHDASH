# Project Management Translation Keys

This document lists all translation keys used in the Project Management module, their English default values, and RTL language support information.

## Translation Architecture

The translation system supports multiple languages with RTL (Right-to-Left) support for Arabic and Farsi. Keys are organized by functional category.

### Supported Languages

| Language | Code | Direction | Status |
|----------|------|-----------|--------|
| English | en | LTR | Default |
| Arabic | ar | RTL | Supported |
| Farsi | fa | RTL | Supported |
| Russian | ru | LTR | Supported |
| Spanish | es | LTR | Supported |

---

## Navigation Keys

Navigation keys are used in menus and navigation elements.

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `project_management` | Project Management | ✓ |
| `project_dashboard` | Project Dashboard | ✓ |
| `project_executive` | Executive Dashboard | ✓ |
| `project_pmo` | PMO Workspace | ✓ |
| `project_portfolio` | Portfolio | ✓ |
| `project_intake` | Project Intake | ✓ |
| `project_list` | Project List | ✓ |
| `project_new` | New Project | ✓ |
| `project_detail` | Project Detail | ✓ |
| `project_edit` | Edit Project | ✓ |
| `project_delete` | Delete Project | ✓ |
| `project_duplicate` | Duplicate Project | — |
| `project_archive` | Archive Project | ✓ |
| `project_restore` | Restore Project | ✓ |
| `project_approval_queue` | Approval Queue | ✓ |
| `project_approved_pipeline` | Approved Pipeline | ✓ |
| `project_active` | Active Projects | ✓ |
| `project_onhold` | On Hold Projects | ✓ |
| `project_completed` | Completed Projects | ✓ |
| `project_cancelled` | Cancelled Projects | ✓ |
| `project_draft` | Draft Projects | ✓ |

---

## Form Labels and Inputs

### Project Basic Information

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `project_code` | Project Code | ✓ |
| `project_name` | Project Name | ✓ |
| `project_description` | Description | ✓ |
| `project_type` | Project Type | ✓ |
| `project_category` | Category | ✓ |
| `project_status` | Status | ✓ |
| `project_priority` | Priority | ✓ |
| `project_owner` | Project Owner | ✓ |
| `project_manager` | Project Manager | ✓ |
| `project_sponsor` | Sponsor | ✓ |
| `project_start_date` | Start Date | ✓ |
| `project_end_date` | End Date | ✓ |
| `project_target_date` | Target Completion Date | ✓ |
| `project_actual_start` | Actual Start Date | ✓ |
| `project_actual_end` | Actual End Date | ✓ |
| `project_baseline_start` | Baseline Start Date | ✓ |
| `project_baseline_end` | Baseline End Date | ✓ |
| `project_progress` | Progress (%) | ✓ |
| `project_cost_center` | Cost Center | ✓ |
| `project_budget_code` | Budget Code | ✓ |
| `project_customer` | Customer | ✓ |
| `project_vendor` | Vendor | ✓ |
| `project_department` | Department | ✓ |
| `project_branch` | Branch | ✓ |
| `project_site` | Site | ✓ |
| `project_notes` | Notes | ✓ |

### Task Fields

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `task_code` | Task Code | ✓ |
| `task_name` | Task Name | ✓ |
| `task_description` | Description | ✓ |
| `task_type` | Task Type | ✓ |
| `task_category` | Category | ✓ |
| `task_status` | Status | ✓ |
| `task_priority` | Priority | ✓ |
| `task_owner` | Task Owner | ✓ |
| `task_assigned_to` | Assigned To | ✓ |
| `task_reviewer` | Reviewer | ✓ |
| `task_phase` | Phase | ✓ |
| `task_wbs` | WBS Element | ✓ |
| `task_start_date` | Start Date | ✓ |
| `task_end_date` | End Date | ✓ |
| `task_duration` | Duration (Days) | ✓ |
| `task_estimated_hours` | Estimated Hours | ✓ |
| `task_actual_hours` | Actual Hours | ✓ |
| `task_progress` | Progress (%) | ✓ |
| `task_milestone` | Associated Milestone | ✓ |
| `task_deliverable` | Deliverable | ✓ |
| `task_blocked` | Blocked | ✓ |
| `task_blocked_reason` | Blocked Reason | ✓ |
| `task_delay_flag` | Delay Flag | ✓ |

### Milestone Fields

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `milestone_code` | Milestone Code | ✓ |
| `milestone_name` | Milestone Name | ✓ |
| `milestone_type` | Type | ✓ |
| `milestone_owner` | Owner | ✓ |
| `milestone_planned_date` | Planned Date | ✓ |
| `milestone_target_date` | Target Date | ✓ |
| `milestone_actual_date` | Actual Completion Date | ✓ |
| `milestone_status` | Status | ✓ |
| `milestone_approval_required` | Approval Required | ✓ |
| `milestone_approved_by` | Approved By | ✓ |
| `milestone_approved_at` | Approved At | ✓ |
| `milestone_is_overdue` | Is Overdue | ✓ |
| `milestone_notes` | Notes | ✓ |

### Budget Fields

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `budget_code` | Budget Code | ✓ |
| `budget_name` | Budget Name | ✓ |
| `budget_type` | Budget Type | ✓ |
| `budget_amount` | Budget Amount | ✓ |
| `budget_spent` | Amount Spent | ✓ |
| `budget_committed` | Committed Amount | ✓ |
| `budget_variance` | Variance | ✓ |
| `budget_variance_percent` | Variance % | ✓ |
| `budget_cost_category` | Cost Category | ✓ |
| `budget_period` | Budget Period | ✓ |
| `budget_approval_status` | Approval Status | ✓ |

### Risk Fields

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `risk_id` | Risk ID | ✓ |
| `risk_title` | Risk Title | ✓ |
| `risk_description` | Description | ✓ |
| `risk_category` | Category | ✓ |
| `risk_probability` | Probability | ✓ |
| `risk_impact` | Impact | ✓ |
| `risk_score` | Risk Score | ✓ |
| `risk_owner` | Owner | ✓ |
| `risk_status` | Status | ✓ |
| `risk_mitigation` | Mitigation Strategy | ✓ |
| `risk_contingency` | Contingency Plan | ✓ |
| `risk_trigger_date` | Trigger Date | ✓ |
| `risk_review_date` | Review Date | ✓ |
| `risk_identified_date` | Date Identified | ✓ |

### Issue Fields

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `issue_number` | Issue Number | ✓ |
| `issue_title` | Issue Title | ✓ |
| `issue_description` | Description | ✓ |
| `issue_category` | Category | ✓ |
| `issue_severity` | Severity | ✓ |
| `issue_impact` | Impact | ✓ |
| `issue_owner` | Owner | ✓ |
| `issue_reported_by` | Reported By | ✓ |
| `issue_reported_date` | Reported Date | ✓ |
| `issue_due_date` | Due Date | ✓ |
| `issue_is_blocker` | Is Blocker | ✓ |
| `issue_status` | Status | ✓ |
| `issue_root_cause` | Root Cause | ✓ |
| `issue_mitigation_plan` | Mitigation Plan | ✓ |
| `issue_escalation_level` | Escalation Level | ✓ |
| `issue_resolution_date` | Resolution Date | ✓ |
| `issue_closure_notes` | Closure Notes | ✓ |

---

## Table Headers

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `table_project_name` | Project Name | ✓ |
| `table_project_code` | Code | ✓ |
| `table_status` | Status | ✓ |
| `table_priority` | Priority | ✓ |
| `table_manager` | Manager | ✓ |
| `table_owner` | Owner | ✓ |
| `table_sponsor` | Sponsor | ✓ |
| `table_progress` | Progress | ✓ |
| `table_start_date` | Start Date | ✓ |
| `table_end_date` | End Date | ✓ |
| `table_days_remaining` | Days Remaining | ✓ |
| `table_days_overdue` | Days Overdue | ✓ |
| `table_actual_hours` | Actual Hours | ✓ |
| `table_estimated_hours` | Estimated Hours | ✓ |
| `table_variance` | Variance | ✓ |
| `table_tasks_total` | Total Tasks | ✓ |
| `table_tasks_completed` | Completed Tasks | ✓ |
| `table_milestones_total` | Total Milestones | ✓ |
| `table_milestones_completed` | Completed Milestones | ✓ |
| `table_open_issues` | Open Issues | ✓ |
| `table_open_risks` | Open Risks | ✓ |
| `table_blockers` | Blockers | ✓ |
| `table_actions` | Actions | ✓ |
| `table_created` | Created | ✓ |
| `table_updated` | Updated | ✓ |
| `table_created_by` | Created By | ✓ |
| `table_modified_by` | Modified By | ✓ |
| `table_select_all` | Select All | ✓ |
| `table_no_data` | No data available | ✓ |
| `table_showing` | Showing | ✓ |
| `table_of` | of | ✓ |
| `table_records` | records | ✓ |
| `table_filter` | Filter | ✓ |
| `table_export` | Export | ✓ |
| `table_search` | Search | ✓ |
| `table_clear_filters` | Clear Filters | ✓ |
| `table_apply_filters` | Apply Filters | ✓ |
| `table_columns` | Columns | ✓ |
| `table_rows` | Rows | ✓ |
| `table_previous` | Previous | ✓ |
| `table_next` | Next | ✓ |
| `table_first` | First | ✓ |
| `table_last` | Last | ✓ |
| `table_overdue` | Overdue | ✓ |

---

## Button Labels

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `button_create` | Create | ✓ |
| `button_save` | Save | ✓ |
| `button_cancel` | Cancel | ✓ |
| `button_delete` | Delete | ✓ |
| `button_edit` | Edit | ✓ |
| `button_view` | View | ✓ |
| `button_copy` | Copy | ✓ |
| `button_duplicate` | Duplicate | ✓ |
| `button_archive` | Archive | ✓ |
| `button_restore` | Restore | ✓ |
| `button_export` | Export | ✓ |
| `button_import` | Import | ✓ |
| `button_submit` | Submit | ✓ |
| `button_approve` | Approve | ✓ |
| `button_reject` | Reject | ✓ |
| `button_hold` | Put On Hold | ✓ |
| `button_resume` | Resume | ✓ |
| `button_complete` | Complete | ✓ |
| `button_close` | Close | ✓ |
| `button_add` | Add | ✓ |
| `button_remove` | Remove | ✓ |
| `button_upload` | Upload | ✓ |
| `button_download` | Download | ✓ |
| `button_preview` | Preview | ✓ |
| `button_print` | Print | ✓ |
| `button_refresh` | Refresh | ✓ |
| `button_assign` | Assign | ✓ |
| `button_reassign` | Reassign | ✓ |
| `button_comment` | Comment | ✓ |
| `button_attach` | Attach File | ✓ |
| `button_sign_off` | Sign Off | ✓ |
| `button_escalate` | Escalate | ✓ |
| `button_delegate` | Delegate | ✓ |
| `button_update` | Update | ✓ |
| `button_filter` | Filter | ✓ |
| `button_configure` | Configure | ✓ |
| `button_schedule` | Schedule | ✓ |
| `button_back` | Back | ✓ |
| `button_next` | Next | ✓ |
| `button_finish` | Finish | ✓ |
| `button_confirm` | Confirm | ✓ |

---

## Status Values

### Project Status

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `status_draft` | Draft | ✓ |
| `status_active` | Active | ✓ |
| `status_on_hold` | On Hold | ✓ |
| `status_completed` | Completed | ✓ |
| `status_cancelled` | Cancelled | ✓ |
| `status_archived` | Archived | ✓ |
| `status_pending_approval` | Pending Approval | ✓ |
| `status_in_review` | In Review | ✓ |

### Task Status

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `task_status_draft` | Draft | ✓ |
| `task_status_open` | Open | ✓ |
| `task_status_in_progress` | In Progress | ✓ |
| `task_status_in_review` | In Review | ✓ |
| `task_status_pending_verification` | Pending Verification | ✓ |
| `task_status_completed` | Completed | ✓ |
| `task_status_cancelled` | Cancelled | ✓ |
| `task_status_blocked` | Blocked | ✓ |

### Priority Levels

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `priority_critical` | Critical | ✓ |
| `priority_high` | High | ✓ |
| `priority_medium` | Medium | ✓ |
| `priority_low` | Low | ✓ |

### Risk Probability

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `probability_very_low` | Very Low | ✓ |
| `probability_low` | Low | ✓ |
| `probability_medium` | Medium | ✓ |
| `probability_high` | High | ✓ |
| `probability_very_high` | Very High | ✓ |

### Risk Impact

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `impact_very_low` | Very Low | ✓ |
| `impact_low` | Low | ✓ |
| `impact_medium` | Medium | ✓ |
| `impact_high` | High | ✓ |
| `impact_very_high` | Very High | ✓ |

### Issue Severity

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `severity_critical` | Critical | ✓ |
| `severity_high` | High | ✓ |
| `severity_medium` | Medium | ✓ |
| `severity_low` | Low | ✓ |

### Resource Status

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `allocation_allocated` | Allocated | ✓ |
| `allocation_available` | Available | ✓ |
| `allocation_overallocated` | Over-allocated | ✓ |
| `allocation_underutilized` | Under-utilized | ✓ |
| `allocation_unavailable` | Unavailable | ✓ |

---

## Messages and Notifications

### Success Messages

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `notification_project_created` | Project created successfully | ✓ |
| `notification_project_updated` | Project updated successfully | ✓ |
| `notification_project_deleted` | Project deleted successfully | ✓ |
| `notification_project_approved` | Project approved successfully | ✓ |
| `notification_project_rejected` | Project rejected | ✓ |
| `notification_project_completed` | Project marked as completed | ✓ |
| `notification_task_created` | Task created successfully | ✓ |
| `notification_task_updated` | Task updated successfully | ✓ |
| `notification_task_completed` | Task completed successfully | ✓ |
| `notification_milestone_completed` | Milestone completed | ✓ |
| `notification_document_uploaded` | Document uploaded successfully | ✓ |
| `notification_export_complete` | Export completed successfully | ✓ |

### Error Messages

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `error_project_not_found` | Project not found | ✓ |
| `error_task_not_found` | Task not found | ✓ |
| `error_milestone_not_found` | Milestone not found | ✓ |
| `error_permission_denied` | Permission denied | ✓ |
| `error_invalid_date_range` | Invalid date range | ✓ |
| `error_required_field` | This field is required | ✓ |
| `error_invalid_format` | Invalid format | ✓ |
| `error_save_failed` | Failed to save | ✓ |
| `error_delete_failed` | Failed to delete | ✓ |
| `error_export_failed` | Export failed | ✓ |
| `error_upload_failed` | Upload failed | ✓ |
| `error_import_failed` | Import failed | ✓ |

### Confirmation Messages

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `confirm_delete_project` | Are you sure you want to delete this project? | ✓ |
| `confirm_delete_task` | Are you sure you want to delete this task? | ✓ |
| `confirm_archive_project` | Are you sure you want to archive this project? | ✓ |
| `confirm_complete_task` | Mark this task as completed? | ✓ |
| `confirm_approve_project` | Approve this project? | ✓ |
| `confirm_reject_project` | Reject this project? | ✓ |
| `confirm_cancel_project` | Cancel this project? | ✓ |

---

## Report Labels

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `report_status` | Project Status Report | ✓ |
| `report_wbs` | WBS Report | ✓ |
| `report_milestones` | Milestone Report | ✓ |
| `report_resources` | Resource Utilization Report | ✓ |
| `report_budget` | Budget vs Actual Report | ✓ |
| `report_risks` | Risk Register Report | ✓ |
| `report_issues` | Issue Log Report | ✓ |
| `report_changes` | Change Request Report | ✓ |
| `report_deliverables` | Deliverables Report | ✓ |
| `report_health` | Project Health Report | ✓ |
| `report_portfolio` | Portfolio Summary Report | ✓ |
| `report_pmo` | PMO Dashboard Report | ✓ |
| `report_executive_summary` | Executive Summary | ✓ |
| `report_detailed_status` | Detailed Status | ✓ |
| `report_health_dashboard` | Health Dashboard | ✓ |
| `report_budget_summary` | Budget Summary | ✓ |
| `report_cost_breakdown` | Cost Breakdown | ✓ |
| `report_forecast` | Forecast Report | ✓ |
| `report_milestones_report` | Milestones Report | ✓ |
| `report_gantt_chart` | Gantt Chart | ✓ |
| `report_slippage` | Slippage Report | ✓ |
| `report_risk_register` | Risk Register | ✓ |
| `report_issue_log` | Issue Log | ✓ |
| `report_change_requests` | Change Requests | ✓ |
| `report_activity_log` | Activity Log | ✓ |
| `reports_subtitle` | Generate and export project reports | ✓ |
| `report_generate` | Generate Report | ✓ |
| `report_schedule` | Schedule Report | ✓ |
| `report_export_format` | Export Format | ✓ |

---

## WBS and Schedule Terms

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `wbs_code` | WBS Code | ✓ |
| `wbs_name` | WBS Name | ✓ |
| `wbs_level` | Level | ✓ |
| `wbs_parent` | Parent | ✓ |
| `wbs_add_node` | Add WBS Node | ✓ |
| `wbs_edit_node` | Edit WBS Node | ✓ |
| `wbs_delete_node` | Delete WBS Node | ✓ |
| `wbs_move_up` | Move Up | ✓ |
| `wbs_move_down` | Move Down | ✓ |
| `wbs_indent` | Indent | ✓ |
| `wbs_outdent` | Outdent | ✓ |
| `schedule_timeline` | Timeline | ✓ |
| `schedule_gantt` | Gantt Chart | ✓ |
| `schedule_critical_path` | Critical Path | ✓ |
| `schedule_baseline` | Baseline | ✓ |
| `schedule_variance` | Schedule Variance | ✓ |
| `schedule_slippage` | Slippage | ✓ |

---

## Governance Terms

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `governance_charter` | Project Charter | ✓ |
| `governance_approval` | Approval | ✓ |
| `governance_sign_off` | Sign Off | ✓ |
| `governance_review` | Review | ✓ |
| `governance_compliance` | Compliance | ✓ |
| `governance_stakeholder` | Stakeholder | ✓ |
| `governance_stakeholder_register` | Stakeholder Register | ✓ |
| `governance_lessons_learned` | Lessons Learned | ✓ |
| `governance_closeout` | Closeout | ✓ |
| `governance_status_update` | Status Update | ✓ |
| `governance_weekly_report` | Weekly Status Report | ✓ |

---

## PMO Terms

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `pmo_workspace` | PMO Workspace | ✓ |
| `pmo_dashboard` | PMO Dashboard | ✓ |
| `pmo_policies` | PMO Policies | ✓ |
| `pmo_processes` | PMO Processes | ✓ |
| `pmo_templates` | PMO Templates | ✓ |
| `pmo_methodology` | Methodology | ✓ |
| `pmo_maturity` | Maturity Level | ✓ |
| `pmo_value_delivered` | Value Delivered | ✓ |
| `pmo_performance` | PMO Performance | ✓ |
| `pmo_metrics` | PMO Metrics | ✓ |

---

## Validation Messages

| Key | English Default Value | RTL |
|-----|----------------------|-----|
| `validation_project_code_required` | Project code is required | ✓ |
| `validation_project_name_required` | Project name is required | ✓ |
| `validation_start_date_required` | Start date is required | ✓ |
| `validation_end_date_required` | End date is required | ✓ |
| `validation_manager_required` | Project manager is required | ✓ |
| `validation_invalid_dates` | End date must be after start date | ✓ |
| `validation_budget_positive` | Budget must be a positive number | ✓ |
| `validation_progress_range` | Progress must be between 0 and 100 | ✓ |
| `validation_task_name_required` | Task name is required | ✓ |
| `validation_assigned_required` | Assignee is required | ✓ |
| `validation_milestone_date_required` | Milestone date is required | ✓ |
| `validation_risk_title_required` | Risk title is required | ✓ |
| `validation_issue_title_required` | Issue title is required | ✓ |

---

## RTL Language Notes

Right-to-Left (RTL) languages (Arabic, Farsi) require special handling for:

1. **Text Direction**: The `direction` property should be set to `rtl` for Arabic and Farsi
2. **Text Alignment**: Right-aligned text for RTL languages
3. **Icons**: Icons that imply direction (arrows, etc.) should be mirrored
4. **Numbers**: Numbers are always displayed LTR, even in RTL context
5. **Dates**: Date formats follow locale conventions
6. **Currency**: Currency symbols position follows locale conventions

### RTL Implementation Example

```javascript
// In templates, check direction:
direction: '{{ direction }}'  // 'rtl' or 'ltr'

// For text alignment:
text-align: {% if direction == 'rtl' %} right {% else %} left {% endif %};

// For icons with direction:
.icon-arrow { transform: scaleX({% if direction == 'rtl' %} -1 {% else %} 1 {% endif %}); }
```

---

## Category Organization Summary

| Category | Key Count | Languages Supported |
|----------|-----------|---------------------|
| Navigation | 25+ | All 5 |
| Form Labels | 50+ | All 5 |
| Table Headers | 30+ | All 5 |
| Buttons | 40+ | All 5 |
| Status Values | 35+ | All 5 |
| Messages | 25+ | All 5 |
| Reports | 30+ | All 5 |
| WBS/Schedule | 15+ | All 5 |
| Governance | 15+ | All 5 |
| PMO | 10+ | All 5 |
| Validation | 15+ | All 5 |

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
