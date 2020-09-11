import os
import requests
from util.const import config
from datetime import datetime


def send_request(url, method, data, headers):
    params = None
    json = None
    param_data = None
    if method == "get":
        params = data
    else:
        json = data

    response = requests.request(
        str.upper(method), url, json=json, params=params, data=param_data, headers=headers)

    status_code = response.status_code
    if status_code >= 400:
        raise requests.HTTPError("%s for %s" % (
            response.status_code, response.url), response=response)
    try:
        result = response.json()
    except ValueError:
        print("result is not a valid json format!!!")
    else:
        return result
    return None


def call_github_api(url, method, data=None, headers={}):
    final_url = "{}{}".format(config["GITHUB_URL"], url)

    final_headers = {
        "Authorization": "token %s" % config["GITHUB_TOKEN"]
    }
    if headers is not None:
        final_headers.update(headers)
    return send_request(final_url, method, data, final_headers)


def call_github_api_v4(query, variables):
    final_url = "{}{}".format(config["GITHUB_URL"], "/graphql")

    final_headers = {
        "Authorization": "bearer %s" % config["GITHUB_TOKEN"]
    }
    data = {
        "query": query,
        "variables": variables
    }

    result = send_request(final_url, "post", data, final_headers)
    if "errors" in result:
        raise Exception(result["errors"][0])
    return result["data"]


def call_ones_api(url, method, product, data=None, headers={}):
    import pprint
    pprint.pprint(product)
    base_url = config["ONES_API_URL"].format(product=product)
    final_url = "{}{}".format(base_url, url)

    if method == "post":
        headers.update({
            "Content-type": "application/json"
        })
    try:
        start_time = datetime.now()
        
        result = send_request(final_url, method, data, headers)

        end_time = datetime.now()
        cost = end_time - start_time
        print("url: {} ,cost:{}".format(url, cost.total_seconds() * 1000))
        return result
    except requests.HTTPError as e:
        response = e.response
        try:
            result = response.json()
        except ValueError:
            raise e
        else:
            raise requests.HTTPError("""
    errcode: %s,
    message: %s,
    request data: %s
            """ % (result["errcode"], e, data), response=response)
