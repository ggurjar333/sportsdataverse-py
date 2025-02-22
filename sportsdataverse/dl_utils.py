import json
import logging
import re
import time
from itertools import chain, starmap

import numpy as np
import polars as pl
import requests

from sportsdataverse.errors import no_espn_data

logger = logging.getLogger("sdv.dl_utils")
logger.addHandler(logging.NullHandler())


def download(url, params=None, headers=None, proxy=None, timeout=30, num_retries=15, session=None, logger=None):
    session, params, logger = init_request_settings(params, session, logger)
    try:
        response = session.get(url, params=params, proxies=proxy, headers=headers, timeout=timeout)
        response = no_espn_data(response)

    except Exception as e:
        if num_retries == 0:
            logger.error(f"Retry Limit Exceeded: {url} \nparams: {params}\n {e}")

        if hasattr(e, "code") and getattr(e, "code") == 404:
            logger.error(f"404: {url} \nparams: {params}")

        if num_retries > 0:
            logger.warning("%s: %i - %s for url (%s)", e, response.status_code, response.reason, response.url)
            time.sleep(2)
            return download(
                url,
                params=params,
                proxy=proxy,
                headers=headers,
                timeout=timeout,
                num_retries=num_retries - 1,
                session=session,
                logger=logger,
            )
        else:
            logger.error(f"Download Error: {url} \nparams: {params}\n {e}")

    return response


def init_request_settings(params, session, logger):
    if params is None:
        params = {}

    if session is None:
        session = requests.Session()

    if logger is None:
        logger = logging.getLogger("sdv.dl_utils")
        logger.addHandler(logging.NullHandler())
    return session, params, logger


def flatten_json_iterative(dictionary, sep=".", ind_start=0):
    """Flattening a nested json file"""

    def unpack_one(parent_key, parent_value):
        """Unpack one level (only one) of nesting in json file"""

        # Unpacking one level

        if isinstance(parent_value, dict):
            for key, value in parent_value.items():
                t1 = parent_key + sep + key

                yield t1, value

        elif isinstance(parent_value, list):
            i = ind_start

            for value in parent_value:
                t2 = parent_key + sep + str(i)

                i += 1

                yield t2, value
        else:
            yield parent_key, parent_value

    # Continue iterating the unpack_one function until the terminating condition is satisfied

    while True:
        # Continue unpacking the json file until all values are atomic elements (aka neither a dictionary nor a list)

        dictionary = dict(chain.from_iterable(starmap(unpack_one, dictionary.items())))

        # Terminating condition: none of the values in the json file are a dictionary or a list

        if not any(isinstance(value, dict) for value in dictionary.values()) and not any(
            isinstance(value, list) for value in dictionary.values()
        ):
            break

    return dictionary


def key_check(obj, key, replacement=np.array([])):
    return obj[key] if key in obj.keys() else replacement


@pl.api.register_dataframe_namespace("janitor")
class ColumnJanitor:
    def __init__(self, df: pl.DataFrame):
        self._df = df

    def clean_names(self) -> pl.DataFrame:
        return self._df.rename({c: underscore(c) for c in self._df.columns})

    def to_pascal_case(self) -> pl.DataFrame:
        return self._df.rename({c: camelize(c, True) for c in self._df.columns})

    def to_camel_case(self) -> pl.DataFrame:
        return self._df.rename({c: camelize(c, False) for c in self._df.columns})

    def to_kebab_case(self) -> pl.DataFrame:
        return self._df.rename({c: kebabize(c) for c in self._df.columns})


def underscore(word):
    """

    Make an underscored, lowercase form from the expression in the string.


    Example::


        >>> underscore("DeviceType")

        'device_type'


    As a rule of thumb you can think of :func:`underscore` as the inverse of

    :func:`camelize`, though there are cases where that does not hold::


        >>> camelize(underscore("IOError"))

        'IoError'


    """

    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", word)

    word = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", word)

    word = word.replace("-", "_")

    return word.lower()


def kebabize(word):
    """

    Make a kebab-case, lowercase form from the expression in the string.


    Example::


        >>> kebabize("DeviceType")

        'device-type'


    As a rule of thumb you can think of :func:`kebabize` as the sister function of

    :func:`underscore`, replacing underscores with dashes

    """

    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", word)

    word = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", word)

    word = word.replace("_", "-")

    return word.lower()


def camelize(string, uppercase_first_letter=True):
    """

    Convert strings to CamelCase.


    Examples::


        >>> camelize("device_type")

        'DeviceType'

        >>> camelize("device_type", False)

        'deviceType'


    :func:`camelize` can be thought of as a inverse of :func:`underscore`,

    although there are some cases where that does not hold::


        >>> camelize(underscore("IOError"))

        'IoError'


    :param uppercase_first_letter: if set to `True` :func:`camelize` converts

        strings to UpperCamelCase. If set to `False` :func:`camelize` produces

        lowerCamelCase. Defaults to `True`.

    """
    if uppercase_first_letter:
        return re.sub(r"(?:^|_)(.)", lambda m: m.group(1).upper(), string)
    else:
        return string[0].lower() + camelize(string)[1:]


class ESPNResponse:
    def __init__(self, response, status_code, url):
        self._response = response

        self._status_code = status_code

        self._url = url

    def get_response(self):
        return self._response

    def get_dict(self):
        return json.loads(self._response)

    def get_json(self):
        return json.dumps(self.get_dict())

    def valid_json(self):
        try:
            self.get_dict()

        except ValueError:
            return False

        return True

    def get_url(self):
        return self._url


class ESPNHTTP:
    espn_response = ESPNResponse

    base_url = None

    parameters = None

    headers = None

    def clean_contents(self, contents):
        return contents

    def send_api_request(
        self, endpoint, parameters, referer=None, headers=None, timeout=None, raise_exception_on_error=False
    ):
        if not self.base_url:
            raise Exception("Cannot use send_api_request from _HTTP class.")

        base_url = self.base_url.format(endpoint=endpoint)

        endpoint = endpoint.lower()

        self.parameters = parameters

        request_headers = self.headers if headers is None else headers
        if referer:
            request_headers["Referer"] = referer

        url = None

        status_code = None

        contents = None

        # Sort parameters by key... for some reason this matters for some requests...

        parameters = sorted(parameters.items(), key=lambda kv: kv[0])

        if not contents:
            response = requests.get(url=base_url, params=parameters, headers=request_headers, timeout=timeout)

            url = response.url

            status_code = response.status_code

            contents = response.text

        contents = self.clean_contents(contents)

        data = self.espn_response(response=contents, status_code=status_code, url=url)

        if raise_exception_on_error and not data.valid_json():
            raise Exception("InvalidResponse: Response is not in a valid JSON format.")

        return data
