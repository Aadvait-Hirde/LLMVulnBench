from marshmallow import Schema, fields, validate, ValidationError, validates

class InferenceRequestSchema(Schema):
    features = fields.List(
        fields.Float(),
        required=True,
        validate=validate.Length(min=1, max=1000),
        error_messages={
            "required": "Features field is required",
            "invalid": "Features must be a list of numbers"
        }
    )
    
    @validates('features')
    def validate_features(self, value):
        if not isinstance(value, list):
            raise ValidationError("Features must be a list")
        if len(value) == 0:
            raise ValidationError("Features list cannot be empty")
        if len(value) > 1000:
            raise ValidationError("Features list cannot exceed 1000 elements")
        for item in value:
            if not isinstance(item, (int, float)):
                raise ValidationError("All features must be numbers")
            if not (-1e10 <= item <= 1e10):
                raise ValidationError("Feature values must be within reasonable range")
