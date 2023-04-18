#!/usr/bin/env python3

import paramiko
import re
import socket
from dotenv import load_dotenv
from tabulate import tabulate
from colorama import Fore, Style, init

def load_target_variables():
    import os

    def load_env_file(env_file_path):
        if not os.path.exists(env_file_path):
            print(f"Error: Unable to find or open {env_file_path}")
            exit(1)

        load_dotenv(dotenv_path=env_file_path)

    def get_env_var(key):
        try:
            value = os.environ[key]
        except KeyError:
            print(f"Error: {key} not found in .env file")
            exit(1)
        return value

    # Load variables from .env file
    load_env_file(".env")

    # Read variables with error handling
    hostname = get_env_var("HOSTNAME")
    username = get_env_var("USERNAME")
    password = get_env_var("PASSWORD")

    return [hostname, username, password]


def get_dict_from_yaml():

    import yaml
    from pathlib import Path

    yaml_dict = {}

    def load_yaml_file(file_path):
        try:
            with open(file_path, 'r') as file:
                yaml_dict = yaml.safe_load(file)
                return yaml_dict
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}")
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML format in {file_path} - {e}")

    file_path = 'cis-benchmarks.yaml'

    yaml_dict = load_yaml_file(file_path)

    # if yaml_dict is not None:
    #     print("YAML file loaded successfully:")
    #     print(yaml_dict)

    return yaml_dict


def filter_trash(cis_dict, auditpol_dict):

    missing_in_auditpol = {}
    missing_in_cis = {}

    for category, subcategories in cis_dict.items():
        if category not in auditpol_dict:
            missing_in_auditpol[category] = set(subcategories.keys())
        else:
            for subcategory in subcategories:
                if subcategory not in auditpol_dict[category]:
                    if category not in missing_in_auditpol:
                        missing_in_auditpol[category] = set()
                    missing_in_auditpol[category].add(subcategory)

    for category, subcategories in auditpol_dict.items():
        if category not in cis_dict:
            missing_in_cis[category] = set(subcategories.keys())
        else:
            for subcategory in subcategories:
                if subcategory not in cis_dict[category]:
                    if category not in missing_in_cis:
                        missing_in_cis[category] = set()
                    missing_in_cis[category].add(subcategory)

    for category, subcategories in list(cis_dict.items()):
        if category not in auditpol_dict:
            del cis_dict[category]
        else:
            for subcategory in list(subcategories.keys()):
                if subcategory not in auditpol_dict[category]:
                    del cis_dict[category][subcategory]

    for category, subcategories in list(auditpol_dict.items()):
        if category not in cis_dict:
            del auditpol_dict[category]
        else:
            for subcategory in list(subcategories.keys()):
                if subcategory not in cis_dict[category]:
                    del auditpol_dict[category][subcategory]

    return [auditpol_dict, cis_dict, missing_in_auditpol, missing_in_cis]


def test_audit_policy():

    secrets = load_target_variables()
    hostname, username, password = secrets

    # Set up SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def check_ssh_availability(host, port=22, timeout=10):
        try:
            sock = socket.create_connection((host, port), timeout)
            sock.close()
            return True
        except socket.error:
            return False

    if not check_ssh_availability(hostname):
        print("[" + Fore.RED + "fail" + Style.RESET_ALL + "] SSH service is not available on the specified "
                                                          "hostname/IP address. Either an invalid host was "
                                                          "specified or SSH is down or firewalled on the specified "
                                                          "target.")
        exit()

    try:
        # Authenticate to Windows Server
        ssh.connect(hostname, username=username, password=password, timeout=10)

    except paramiko.AuthenticationException:
        print("[" + Fore.RED + "fail" + Style.RESET_ALL + "] Error: SSH Authentication failed. Please check your "
                                                          "username and password.")
    except paramiko.SSHException:
        print("[" + Fore.RED + "fail" + Style.RESET_ALL + "] Error: An SSH-related error occurred.")
    except Exception as e:
        print("[" + Fore.RED + "fail" + Style.RESET_ALL + "] " + str(e))
    else:
        # Run the 'auditpol /get /category:*' command over SSH on the remote server
        stdin, stdout, stderr = ssh.exec_command('auditpol /get /category:*')

        error = stderr.read()
        if error:
            print(f"Error encountered: {error.decode('utf-8')}")
            exit(1)

        output = stdout.read().decode('utf-8')

        # Split the string into lines
        lines = output.split('\n')

        # Remove the first two lines and join the remaining lines
        output = '\n'.join(lines[2:])

        text = output
        category_pattern = r'^(\w+.*?)(\r)?$'
        subcategory_pattern = r'^( {2})([^ ]+.*?)(?=\s{3,})(.*\S)'

        auditpol_dict = {}
        current_category = None

        for line in text.split('\n'):
            category_match = re.match(category_pattern, line)
            subcategory_match = re.match(subcategory_pattern, line)

            if category_match:
                current_category = category_match.group(1)
                auditpol_dict[current_category] = {}
            elif subcategory_match:
                subcategory = subcategory_match.group(2).strip()
                setting = subcategory_match.group(3).strip()
                auditpol_dict[current_category][subcategory] = setting

        cis_dict = get_dict_from_yaml()

        filter_result = filter_trash(cis_dict, auditpol_dict)
        auditpol_dict = filter_result[0]
        cis_dict = filter_result[1]
        in_cisyaml_but_missing_from_auditpol = filter_result[2]
        in_auditpol_but_missing_from_cisyaml = filter_result[3]

        results = {}

        for main_key in auditpol_dict:
            results[main_key] = {}
            for sub_key in auditpol_dict[main_key]:
                if auditpol_dict[main_key][sub_key] == cis_dict[main_key][sub_key]['CIS Recommended']:
                    results[main_key][sub_key] = {'CIS_included': cis_dict[main_key][sub_key]['CIS Benchmark'],
                                                  'result_expected': cis_dict[main_key][sub_key]['CIS Recommended'],
                                                  'result': auditpol_dict[main_key][sub_key],
                                                  'verdict': 'pass'}
                else:
                    results[main_key][sub_key] = {'CIS_included': cis_dict[main_key][sub_key]['CIS Benchmark'],
                                                  'result_expected': cis_dict[main_key][sub_key]['CIS Recommended'],
                                                  'result': auditpol_dict[main_key][sub_key],
                                                  'verdict': 'fail'}

        init(autoreset=True)  # Automatically reset colorama styles after each print

        headers = ["Category", "Subcategory", "CIS Benchmark?", "Test Result (result [expected])", "Verdict"]

        table_data = []
        cis_benchmark_count = 0
        cis_benchmark_pass_count = 0

        for category, subcategories in results.items():
            for subcategory, details in subcategories.items():
                CIS_included = details['CIS_included']
                result = details['result']
                result_expected = details['result_expected']
                verdict = details['verdict']

                if verdict == 'fail':
                    colored_verdict = Fore.RED + verdict + Style.RESET_ALL
                elif verdict == 'pass':
                    colored_verdict = Fore.GREEN + verdict + Style.RESET_ALL
                else:
                    colored_verdict = verdict

                if CIS_included:
                    cis_benchmark_count += 1
                    if verdict == 'pass':
                        cis_benchmark_pass_count += 1

                table_data.append(
                    [category, subcategory, CIS_included, f"{result} [{result_expected}]", colored_verdict])

        print(tabulate(table_data, headers=headers, tablefmt='grid'))

        # Print the final score
        print("\n")
        print(f"CIS Benchmarks Test Score: {cis_benchmark_pass_count} / {cis_benchmark_count}")

        if in_cisyaml_but_missing_from_auditpol:
            print("\n")
            print("Note: some [Sub]categories were found to be in the CIS Benchmarks YAML file, but could not"
                  " be matched with output [Sub]categories from the auditpol command:")
            for category, subcategory in in_cisyaml_but_missing_from_auditpol.items():
                for j in subcategory:
                    print(f"\t{category} --> {j}")

        if in_auditpol_but_missing_from_cisyaml:
            print("\n")
            print("Note: some [Sub]categories were found to be in the auditpol command output, but could not be "
                  "matched with output [Sub]categories from the CIS Benchmarks YAML file:")
            for category, subcategory in in_auditpol_but_missing_from_cisyaml.items():
                for j in subcategory:
                    print(f"\t{category} --> {j}")

    finally:
        # Close the SSH connection
        ssh.close()


if __name__ == '__main__':
    test_audit_policy()
