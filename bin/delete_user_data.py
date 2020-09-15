from __future__ import print_function

#
# A helper script to delete user data from a Sync storage server.
#
# You can use this script to explicitly delete stored sync data
# for a user, without having to connect a Firefox profile and
# without having to reset their password.  It may be useful if
# you've started running a self-hosted storage server and want
# to delete data that was previously stored on the Mozilla-hosted
# servers.
#
# Use it like so:
#
#    $> pip install PyFxA
#    $> python delete_user_data.py user@example.com
#
# The script makes a best-effort attempt to sign in to the user's
# account, authenticate to the Firefox Sync Tokenserver, and delete
# the user's stored sync data.  The login process might fail due to
# things like rate-limiting, server-side security measures, or API
# changes in the login process.
#

import sys
import getpass
import hashlib
import argparse

import requests
import hawkauthlib
import fxa.core


try:
    # python 2 support
    from urlparse import urlparse, parse_qs, urljoin
except ModuleNotFoundError:
    # python 3 support
    from urllib.parse import urlparse, parse_qs, urljoin
    from six.moves import input as raw_input


DEFAULT_FXA_URI = "https://api.accounts.firefox.com"
DEFAULT_TOKENSERVER_URI = "https://token.services.mozilla.com"


def main(argv):
    parser = argparse.ArgumentParser(description="Delete Firefox Sync data")
    parser.add_argument("email",
                        help="Email of the account for which to delete data")
    parser.add_argument("--accounts-uri", default=DEFAULT_FXA_URI,
                        help="URI of the Firefox Accounts API server")
    parser.add_argument("--tokenserver-uri", default=DEFAULT_TOKENSERVER_URI,
                        help="URI of the Firefox Sync tokenserver")

    args = parser.parse_args(argv)

    # Sign in to the account.
    c = fxa.core.Client(args.accounts_uri)
    password = getpass.getpass("Password for {}: ".format(args.email))
    s = c.login(args.email, password, keys=True)
    try:
        # Verify the session if necessary.
        # TODO: this won't work if the user has enabled two-step auth.
        status = s.get_email_status()
        if not status["sessionVerified"]:
            if s.verificationMethod == "totp-2fa":
                code = raw_input("Enter TOTP code: ")
                s.totp_verify(code)
            else:
                code = raw_input(
                    "Enter verification link or code received via email: ")
                if "?" in code:
                    # They copy-pasted the full URL.
                    code_url = urlparse(code)
                    code = parse_qs(code_url.query)["code"][0]
                s.verify_email_code(code)

        # Prepare authentication details for tokenserver.
        (_, kB) = s.fetch_keys()
        xcs = hashlib.sha256(kB).hexdigest()[:32]
        auth = s.get_identity_assertion(args.tokenserver_uri)

        # Auth to tokenserver, find sync storage node.
        token_uri = urljoin(args.tokenserver_uri, "1.0/sync/1.5")
        r = requests.get(token_uri, headers={
            "Authorization": "BrowserID " + auth,
            "X-Client-State": xcs,
        })
        r.raise_for_status()

        node = r.json()
        api_endpoint = node["api_endpoint"]
        hawk_id = str(node["id"])
        hawk_key = str(node["key"])
        print("Deleting from", api_endpoint)
        req = requests.Request("DELETE", api_endpoint).prepare()
        hawkauthlib.sign_request(req, hawk_id, hawk_key)
        r = requests.session().send(req)
        r.raise_for_status()
        print(r)
    finally:
        s.destroy_session()


if __name__ == "__main__":
    main(sys.argv[1:])
