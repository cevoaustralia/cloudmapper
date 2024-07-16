
import os
import argparse
import json
import pandas as pd
from pandas import ExcelWriter
import openpyxl
import argparse
from shared.common import get_account, parse_arguments
from .collect import collect
from .find_unused import find_unused_resources

__description__ = "Run AWS API calls to collect data from the account and generates the excel sheet"

MAX_RETRIES = 3

def run(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="Config file name", default="config.json", type=str
    )
    parser.add_argument(
        "--account",
        help="Account to collect from",
        required=False,
        type=str,
        dest="account_name",
    )
    parser.add_argument(
        "--profile",
        help="AWS profile name",
        required=False,
        type=str,
        dest="profile_name",
    )
    parser.add_argument(
        "--clean",
        help="Remove any existing local, previously collected data for the account before gathering",
        action="store_true",
    )
    parser.add_argument(
        "--max-attempts",
        help="Override Botocore config max_attempts (default 4)",
        required=False,
        type=int,
        dest="max_attempts",
        default=4,
    )
    parser.add_argument(
        "--regions",
        help="Filter and query AWS only for the given regions (CSV)",
        required=False,
        type=str,
        dest="regions_filter",
        default="",
    )

    args = parser.parse_args(arguments)

    if not args.account_name:
        try:
            config = json.load(open(args.config))
        except IOError:
            exit('ERROR: Unable to load config file "{}"'.format(args.config))
        except ValueError as e:
            exit(
                'ERROR: Config file "{}" could not be loaded ({}), see config.json.demo for an example'.format(
                    args.config, e
                )
            )
        args.account_name = get_account(args.account_name, config, args.config)["name"]

    _, accounts, config = parse_arguments(arguments)
    
    data = find_unused_resources(accounts)

    with open('unused_resources.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    try:
        json_to_excel(data, 'account-data/data/unused_resources.xlsx', args)
    except:
        print("Error: Unable to create Excel file.")

def json_to_excel(json_data, output_path,args) -> None:
    """
    Converts a list of JSON-like objects to an Excel file.

    Args:
        json_data (list): List of JSON-like objects to convert.
        output_path (str): Path to the output Excel file.

    Returns:
        None
    """
    # Prepare data for Excel
    excel_data = []

    def process_unused_resources(account_id, account_name, region, resources, resource_type):
        for resource in resources:
            entry = {
                'Account ID': account_id,
                'Account Name': account_name,
                'Region': region,
                'Resource Type': resource_type
            }
            entry.update(resource)
            excel_data.append(entry)

    for account in json_data:
        account_id = account.get('account', {}).get('id')
        account_name = account.get('account', {}).get('name')
        for region_info in account.get('regions', []):
            region = region_info.get('region')
            unused_resources = region_info.get('unused_resources', {})
            for resource_type, resources in unused_resources.items():
                process_unused_resources(account_id, account_name, region, resources, resource_type)

    # Convert to DataFrame
    df = pd.DataFrame(excel_data)

    # Save to Excel
    with ExcelWriter(f'account-data/{args.account_name}/unused_resources.xlsx') as writer:
        df.to_excel(writer, index=False)

    print(f"Excel file has been created at {output_path}")