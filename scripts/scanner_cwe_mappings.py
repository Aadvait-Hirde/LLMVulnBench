
"""
Mappings from scanner specific rules to CWE IDs.
Currently focuses on Bandit which often output None for CWEs.
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
    
    # Fallback to manual mapping
    if scanner == 'bandit':
        return BANDIT_RULE_TO_CWE.get(rule_id)
        
    return None
