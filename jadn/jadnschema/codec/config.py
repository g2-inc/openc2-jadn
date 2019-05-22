"""
Codec index names
"""

# Codec Table fields
C_DEC = 0       # Decode function
C_ENC = 1       # Encode function
C_ETYPE = 2     # Encoded type

# Symbol Table fields
S_TDEF = 0      # JADN type definition
S_CODEC = 1     # CODEC table entry for this type
S_STYPE = 2     # Encoded identifier type (string or tag)
S_FORMAT = 3    # Function to check value constraints
S_TOPT = 4      # Type Options (dict format)
S_VSTR = 5      # Verbose_str
S_DMAP = 6      # Decode: Encoded field key or enum value to API
S_EMAP = 7      # Encode: API field key or enum value to Encoded
S_FLD = 8       # Field entries (definition and decoded options)

# Symbol Table Field Definition fields
S_FDEF = 0      # JADN field definition
S_FOPT = 1      # Field Options (dict format)
S_FNAMES = 2    # Possible field names returned from Choice type
