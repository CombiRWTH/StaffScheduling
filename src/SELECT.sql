SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN (
    'TPersonalDienstArten',
    'TPersonalRollmodelle',
    'TPersonalParameter',
    'TPersonalEinsatzorte',
    'TPersonalStatusJeTag'
)
ORDER BY
    TABLE_NAME,
    ORDINAL_POSITION;
