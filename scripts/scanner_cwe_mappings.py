
"""
Mappings from scanner specific rules to CWE IDs.
Covers Bandit (Python), Semgrep (TypeScript/Java), and cppcheck (C++).
"""

BANDIT_RULE_TO_CWE = {
    'B101': 'CWE-703',  # assert_used
    'B102': 'CWE-78',   # exec_used
    'B103': 'CWE-732',  # set_bad_file_permissions
    'B104': 'CWE-200',  # hardcoded_bind_all_interfaces
    'B105': 'CWE-259',  # hardcoded_password_string
    'B106': 'CWE-259',  # hardcoded_password_funcarg
    'B107': 'CWE-259',  # hardcoded_password_default
    'B108': 'CWE-377',  # hardcoded_tmp_directory
    'B110': 'CWE-703',  # try_except_pass
    'B112': 'CWE-703',  # try_except_continue
    'B113': 'CWE-400',  # request_without_timeout
    'B201': 'CWE-215',  # flask_debug_true
    'B202': 'CWE-22',   # tarfile_unsafe_members
    'B301': 'CWE-502',  # pickle
    'B303': 'CWE-327',  # md5
    'B311': 'CWE-330',  # random
    'B324': 'CWE-327',  # hashlib_new_insecure_functions
    'B403': 'CWE-502',  # import_pickle
    'B404': 'CWE-78',   # import_subprocess
    'B413': 'CWE-119',  # import_pycrypto (buffer overflows in pycrypto)
    'B603': 'CWE-78',   # subprocess_without_shell_equals_true
    'B607': 'CWE-78',   # start_process_with_partial_path
    'B608': 'CWE-89',   # hardcoded_sql_expressions
    'B614': 'CWE-94',   # pytorch_load (code injection)
    'B615': 'CWE-494',  # huggingface_unsafe_download
}

# Semgrep rule mappings for TypeScript/JavaScript and Java
# Sources: Semgrep rule metadata, MITRE CWE database, OWASP guidance
SEMGREP_RULE_TO_CWE = {
    # ----- JavaScript/TypeScript rules -----
    # Path traversal via path.join/path.resolve with user input
    'javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal': 'CWE-22',
    # OS command injection via child_process
    'javascript.lang.security.detect-child-process.detect-child-process': 'CWE-78',
    # Hardcoded session secret
    'javascript.express.security.audit.express-session-hardcoded-secret.express-session-hardcoded-secret': 'CWE-798',
    # Missing CSRF middleware
    'javascript.express.security.audit.express-check-csurf-middleware-usage.express-check-csurf-middleware-usage': 'CWE-352',
    # CORS misconfiguration (overly permissive origins)
    'javascript.express.security.cors-misconfiguration.cors-misconfiguration': 'CWE-942',
    # ReDoS via non-literal regexp from user input
    'javascript.lang.security.audit.detect-non-literal-regexp.detect-non-literal-regexp': 'CWE-1333',
    # Unsafe format string (potential injection)
    'javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring': 'CWE-134',
    # Cipher created without IV (insecure cryptography)
    'javascript.node-crypto.security.create-de-cipher-no-iv.create-de-cipher-no-iv': 'CWE-329',
    # GCM mode without specifying tag length (weak crypto)
    'javascript.node-crypto.security.gcm-no-tag-length.gcm-no-tag-length': 'CWE-327',
    # AJV allErrors:true leaks validation info
    'javascript.ajv.security.audit.ajv-allerrors-true.ajv-allerrors-true': 'CWE-209',
    # TLS verification bypass (insecure transport)
    'problem-based-packs.insecure-transport.js-node.bypass-tls-verification.bypass-tls-verification': 'CWE-295',

    # ----- Java rules -----
    # Bad hexadecimal conversion (incorrect type conversion)
    'java.lang.security.audit.bad-hexa-conversion.bad-hexa-conversion': 'CWE-704',
    # CBC padding oracle vulnerability
    'java.lang.security.audit.cbc-padding-oracle.cbc-padding-oracle': 'CWE-327',
    # OS command injection via ProcessBuilder
    'java.lang.security.audit.command-injection-process-builder.command-injection-process-builder': 'CWE-78',
    # Cookie missing HttpOnly flag
    'java.lang.security.audit.cookie-missing-httponly.cookie-missing-httponly': 'CWE-1004',
    # Cookie missing Secure flag
    'java.lang.security.audit.cookie-missing-secure-flag.cookie-missing-secure-flag': 'CWE-614',
    # ECB cipher mode (insecure block cipher mode)
    'java.lang.security.audit.crypto.ecb-cipher.ecb-cipher': 'CWE-327',
    # Use of MD5 (broken hash)
    'java.lang.security.audit.crypto.use-of-md5.use-of-md5': 'CWE-327',
    # Permissive CORS configuration
    'java.lang.security.audit.permissive-cors.permissive-cors': 'CWE-942',
    # Cookie isSecure set to false
    'java.servlets.security.cookie-issecure-false.cookie-issecure-false': 'CWE-614',
    # Spring CSRF protection disabled
    'java.spring.security.audit.spring-csrf-disabled.spring-csrf-disabled': 'CWE-352',
    # Tainted file path (path traversal)
    'java.spring.security.injection.tainted-file-path.tainted-file-path': 'CWE-22',
}

# Cppcheck rule mappings
# Sources: cppcheck documentation, MITRE CWE database
CPPCHECK_RULE_TO_CWE = {
    # Too many branches for normal check level (code complexity indicator)
    'normalCheckLevelMaxBranches': 'CWE-710',  # Improper Adherence to Coding Standards
    # Syntax error in source code
    'syntaxError': 'CWE-710',  # Improper Adherence to Coding Standards
    # Dangerous type cast
    'dangerousTypeCast': 'CWE-704',  # Incorrect Type Conversion or Cast
    # Return value of function ignored
    'ignoredReturnValue': 'CWE-252',  # Unchecked Return Value
    # Incorrect string comparison (using == instead of strcmp)
    'incorrectStringCompare': 'CWE-597',  # Use of Wrong Operator in String Comparison
    # Uninitialized private member variable
    'uninitMemberVarPrivate': 'CWE-457',  # Use of Uninitialized Variable
    # Uninitialized struct member
    'uninitStructMember': 'CWE-457',  # Use of Uninitialized Variable
    # Uninitialized variable
    'uninitvar': 'CWE-457',  # Use of Uninitialized Variable
    # Missing virtual destructor (polymorphism issue)
    'virtualDestructor': 'CWE-710',  # Improper Adherence to Coding Standards
}


def get_cwe_from_rule(scanner, rule_id, reported_cwe=None):
    """
    Returns the CWE ID for a given scanner and rule ID.
    If reported_cwe is provided and valid, it is returned.
    Otherwise, a lookup table is used.
    """
    # If the scanner mapped it, use that (unless it's empty or 'None')
    if reported_cwe and str(reported_cwe).lower() not in ('none', 'nan', ''):
        # Normalize CWE format (Scanner might return "CWE-123" or "123")
        cwe_str = str(reported_cwe).upper().strip()
        if not cwe_str.startswith('CWE-'):
            cwe_str = f'CWE-{cwe_str}'
        return cwe_str
    
    # Fallback to manual mapping by scanner
    if scanner == 'bandit':
        return BANDIT_RULE_TO_CWE.get(rule_id)
    elif scanner == 'semgrep':
        return SEMGREP_RULE_TO_CWE.get(rule_id)
    elif scanner == 'cppcheck':
        return CPPCHECK_RULE_TO_CWE.get(rule_id)
        
    return None
