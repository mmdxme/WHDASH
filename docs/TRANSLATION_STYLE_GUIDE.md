# Translation Style Guide

## Overview
This document defines the standards and guidelines for all translations in the WHDASH enterprise ERP system.

## General Principles

### Accuracy
- All translations must maintain the exact business meaning of the English source
- Technical ERP terms should be translated consistently across all modules
- Never omit or add meaning during translation

### Clarity
- Use clear, professional language appropriate for business users
- Avoid colloquialisms and slang
- Use formal register for all UI elements

### Consistency
- Same English term must be translated the same way throughout all files
- Use the ERP Terminology Glossary for all business terms
- Maintain consistent capitalization patterns per language

---

## Language-Specific Guidelines

### Persian (fa) / Farsi
- **Direction**: RTL (Right-to-Left)
- Use Persian numerals for displayed counts when appropriate
- Maintain ZWNJ (zero-width non-joiner) between Persian text and Latin terms
- Keep ERP abbreviations (ROI, KPI, CRM) in Latin script
- Respect Persian compound word formations
- Use formal Persian business vocabulary

### Arabic (ar)
- **Direction**: RTL (Right-to-Left)
- Use Arabic numerals for displayed counts unless space-limited
- Use appropriate definite article (ال) for generic terms
- Maintain consistent MSA (Modern Standard Arabic) register
- Keep ERP abbreviations in Latin script
- Use appropriate formal business Arabic

### Russian (ru)
- **Direction**: LTR
- Use appropriate informal/formal "you" (ты/вы) - use "вы" for business ERP
- Maintain Cyrillic characters only, no Latin transliteration of Russian terms
- Use appropriate Russian business vocabulary

### Chinese (zh)
- **Direction**: LTR
- Use Simplified Chinese (简体中文) for all UI text
- Keep proper nouns and abbreviations in original script
- Use appropriate formal Chinese register

### Spanish (es)
- **Direction**: LTR
- Use formal "usted" register for business ERP
- Maintain consistent use of formal vs informal address
- Use appropriate Latin American Spanish vocabulary

### Hindi (hi)
- **Direction**: LTR
- Use Devanagari script exclusively
- Use appropriate formal Hindi business vocabulary
- Keep English loanwords that are standard in Indian business context

### German (de)
- **Direction**: LTR
- Use formal "Sie" register for all business communication
- German compound words should be properly combined
- Nouns capitalized as per German rules

---

## ERP Business Terms

All business terms must use the translations defined in `ERP_TERMINOLOGY_GLOSSARY.md`.

Key terms include:
- Campaign / Lead / Funnel (Marketing)
- NCR / CAPA / Inspection (Quality)
- Escalation / Delegation / Workflow (Task Management)
- Invoice / Delivery / Fleet (Operations)

---

## Status and State Labels

| English | Persian | Arabic | Russian | Chinese | Spanish | Hindi | German |
|---------|---------|--------|---------|---------|---------|-------|--------|
| Pending | در انتظار | قيد الانتظار | В ожидании | 待处理 | Pendiente | लंबित | Ausstehend |
| Completed | تکمیل شده | مكتمل | Завершено | 已完成 | Completado | पूर्ण | Abgeschlossen |
| Overdue | overdue | متأخر | Просрочено | 逾期 | Vencido | अतिदेय | Überfällig |
| Draft | پیش‌نویس | مسودة | Черновик | 草稿 | Borrador | ड्राफ्ट | Entwurf |
| Approved | تأیید شده | معتمد | Одобрено | 已批准 | Aprobado | स्वीकृत | Genehmigt |
| Rejected | رد شده | مرفوض | Отклонено | 已拒绝 | Rechazado | अस्वीकृत | Abgelehnt |

---

## Action Verbs

| English | Persian | Arabic | Russian | Chinese | Spanish | Hindi | German |
|---------|---------|--------|---------|---------|---------|-------|--------|
| Create | ایجاد | إنشاء | Создать | 创建 | Crear | बनाना | Erstellen |
| Edit | ویرایش | تعديل | Редактировать | 编辑 | Editar | संपादित | Bearbeiten |
| Delete | حذف | حذف | Удалить | 删除 | Eliminar | हटाना | Löschen |
| Save | ذخیره | حفظ | Сохранить | 保存 | Guardar | सहेजना | Speichern |
| Cancel | لغو | إلغاء | Отмена | 取消 | Cancelar | रद्द | Abbrechen |
| Assign | اختصاص | تعيين | Назначить | 分配 | Asignar | सौंपना | Zuweisen |
| Submit | ارسال | إرسال | Отправить | 提交 | Enviar | जमा | Einreichen |
| Approve | تأیید | موافقة | Одобрить | 批准 | Aprobar | स्वीकृत | Genehmigen |
| Reject | رد | رفض | Отклонить | 拒绝 | Rechazar | अस्वीकृत | Ablehnen |

---

## Capitalization Rules

- **English**: Use sentence case for all UI text (only first word and proper nouns capitalized)
- **Persian/Arabic**: Follow language-specific rules, no capitalization equivalent
- **German**: Nouns always capitalized, other words follow standard rules

---

## Placeholders and Variables

- Use `{0}`, `{1}` format for variable placeholders
- Do not translate placeholder hints like "Enter your {field_name}"
- Maintain HTML markup exactly as provided

---

## Numbers and Dates

| Aspect | Rule |
|--------|------|
| Date Format | Use locale-appropriate format |
| Numbers | Use localized number formatting (commas vs periods) |
| Currency | Keep currency symbol placement locale-appropriate |

---

## RTL/LTR Display Rules

### For RTL Languages (Persian, Arabic):
- All UI elements must flip direction
- Icons that imply direction (arrows) should flip
- Tables flip column order
- Forms flip label/input relationships
- Numbers remain LTR within RTL context
- English/Latin text within RTL context renders correctly

### For LTR Languages:
- No RTL artifacts should appear
- All text renders left-to-right
- Mixed content (Latin in LTR) renders normally

---

## Handling Mixed-Language Text

When the same field contains mixed languages:
1. Keep proper nouns in their original script
2. Keep technical abbreviations (ROI, KPI, NCR, CAPA) in Latin
3. Use appropriate bidirectional text handling
4. In RTL languages, wrap Latin text in appropriate Unicode marks if needed

---

## Translation Priority

1. **Critical (must translate)**: Buttons, menus, form labels, error messages, page titles
2. **High**: Status labels, table headers, notifications, tooltips
3. **Medium**: Help text, descriptions, placeholder text
4. **Low**: Debug messages, technical logs

---

## What NOT to Translate

- Technical error codes
- File paths (keep Latin script)
- Email addresses
- URL paths
- HTML/CSS class names
- JSON/XML key names
- Programming variables
- Database field names

---

## Quality Checklist

Before finalizing any translation:
- [ ] Read the full translated string in context
- [ ] Verify it fits the UI space available
- [ ] Check for any text truncation
- [ ] Verify RTL/LTR rendering is correct
- [ ] Ensure mixed-language strings render correctly
- [ ] Check that abbreviations are consistent
- [ ] Verify status labels match glossary
- [ ] Check button/form labels for appropriate length

---

*Last updated: April 2026*
*Document owner: i18n Team*