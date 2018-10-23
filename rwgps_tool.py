import os
import sys
import getpass
import argparse

import requests

base_params = { 
    'version' : 2
}

rwgps_base_url = 'https://ridewithgps.com/'

def request_rwgps(url_partial, params):
    return requests.get(rwgps_base_url + url_partial, params=params)

def user_auth(email, password, params):
    params = base_params.copy()
    params['email'] = email
    params['password'] = password
    r = request_rwgps('users/current.json', params)
    if r.status_code == 200:
        results = r.json()
        return results['user']
    else:
        return None

def get_club_id_by_name(clubs, club_name):
    for c in clubs:
        if c['name'] == club_name:
            return c['id']
    return None

def iter_club(dump_club, dump_routes, dump_route):
    r = request_rwgps('users/{0}/clubs.json'.format(user_id), auth_params)
    if r.status_code != 200:
        err_print('unable to retrieve your clubs')
        exit(1)
    clubs = r.json()
    
    if args.club_name == None and args.club_id == None:
        print('Clubs:')
        for c in clubs['results']:
            print('\t{0} ({1})'.format(c['name'], c['id']))
        exit(1)
    
    if args.club_name:
        club_id = get_club_id_by_name(clubs['results'], args.club_name)
    else:
        club_id = args.club_id
    
    r = request_rwgps('clubs/{0}.json'.format(club_id), auth_params)
    if r.status_code != 200:
        err_print('unable to get club details')
        exit(1)
    club_detail = r.json()
    dump_club(club_detail, r.text)
    
    routes_params = auth_params.copy()
    routes_params['limit'] = 2000
    r = request_rwgps('clubs/{0}/routes.json'.format(club_id), routes_params)
    if r.status_code != 200:
        err_print('unable to get club routes')
        exit(1)
    club_routes = r.json()
    dump_routes(club_routes, r.text)
    
    route_details = {}

    for cr in club_routes['results']:
        route_id = cr['id']
        r = request_rwgps('routes/{0}.json'.format(route_id), auth_params)
        if r.status_code != 200:
            err_print('unable to get route {0}'.format(route_id))
        else:
            dump_route(route_id, r.json(), r.text)
    
# deliberately not interpreting the data
def dump_to_file(buf, name):
    with open(name, "w") as file:
        file.write(buf)

def backup_club():
    def dump_club(json, text):
        dump_to_file(text, 'club_detail.json')

    def dump_routes(json, text):
        dump_to_file(text, 'club_routes.json')

    def dump_route(route_id, json, text):
        dump_to_file(text, '{0}.json'.format(route_id))

    iter_club(dump_club, dump_routes, dump_route)

def err_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser(description='rwgps tool')
parser.add_argument('--backupclub', action='store_true', required=True)
parser.add_argument('--email', type=str, required=True)
parser.add_argument('--password', type=str, default=None)
parser.add_argument('--apikey', type=str, required=True)
group = parser.add_mutually_exclusive_group()
group.add_argument('--club-name', type=str)
group.add_argument('--club-id', type=str)

args = parser.parse_args()

base_params['apikey'] = args.apikey

if args.password == None:
    password = getpass.getpass()
else:
    password = args.password

user = user_auth(args.email, password, base_params)
if user == None:
    err_print('failed login')
    exit(1)

user_id = user['id']

auth_params = base_params.copy()
auth_params['auth_token'] = user['auth_token']

if args.backupclub:
    backup_club()

