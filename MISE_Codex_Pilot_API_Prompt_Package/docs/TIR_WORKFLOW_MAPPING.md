# TIR Workflow Mapping

## Intake

A client submits project details through a Smartsheet form. The pilot reads the resulting row and normalizes it into the internal TIR model.

## Registry

The Registry Database is treated as the operational source for MISE file references, project status, contact details, project background, funding source, and responsible officer routing.

## Secretary decision path

The pilot must not make approval decisions automatically. It reads Secretary approval and status values. In future controlled write-back, it may update integration metadata, folder links, and reconciliation status, but must not alter the Secretary approval decision.

## Project folder linkage

After approval and dry-run review, the service may create or link a project folder using the registry file reference and project name.

## Reporting

The service extracts normalized project data and produces reports by department, funding source, status, location, service request, and data quality status.
