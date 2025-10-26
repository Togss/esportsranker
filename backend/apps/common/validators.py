from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date

TEAM_SHORT_NAME_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9]{3,5}$',
    message='Team short name must be 3-5 alphanumeric characters.'
)
    
NATIONALITY_VALIDATOR = RegexValidator(
    regex=r'^[A-Z]{2}$',
    message='Nationality must be a valid ISO 3166-1 alpha-2 country code (2 uppercase letters).'
)

# ----------------------------------------------------------------------------
# Additional validators can be added here as needed
# ----------------------------------------------------------------------------
def validate_year_range(value, min_year=1850, max_year=2100):
    if value is None:
        return
    if value < min_year or value > max_year:
        raise ValidationError(
            f'Year must be between {min_year} and {max_year}.'
        )
    
def validate_start_before_end(
        start_date,
        end_date,
        field_start='start_date',
        field_end='end_date'
):
    if end_date and start_date and end_date < start_date:
        raise ValidationError(
            {field_end: f'{field_end.replace("_", " ").capitalize()} must be after {field_start.replace("_", " ")}.'}
        )
    
def validate_membership_overlap(
        subject,
        start_date,
        end_date,
        current_pk,
        queryset,
        subject_field_name: str,
        overlap_error_message: str,

):
    a_start = start_date
    a_end = end_date or date.max

    overlapping = queryset.filter(
        **{subject_field_name: subject}
    ).exclude(pk=current_pk)

    for m in overlapping:
        b_start = m.start_date
        b_end = m.end_date or date.max

        if a_start <= b_end and b_start <= a_end:
            raise ValidationError(
                overlap_error_message
            )
        
def validate_child_dates_within_parent(
        child_start,
        child_end,
        parent_start,
        parent_end,
        parent_label='parent range',
        field_start='start_date',
        field_end='end_date',
):
    errors = {}
    if child_start and parent_start and child_start < parent_start:
        errors[field_start] = f'{field_start.replace("_", " ").capitalize()} must be on or after {parent_label} start date.'
    if child_end and parent_end and child_end > parent_end:
        errors[field_end] = f'{field_end.replace("_", " ").capitalize()} must be on or before {parent_label} end date.'
    if errors:
        raise ValidationError(errors)
    
def validate_same_tournament(
        stage_tournament_id,
        series_tournament_id,
):
    if (
        stage_tournament_id
        and series_tournament_id
        and stage_tournament_id != series_tournament_id
    ):
        raise ValidationError({
            'stage': 'Stage tournament must match series tournament.'
        })