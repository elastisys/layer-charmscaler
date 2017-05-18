#!/usr/bin/env python3.5
import amulet
import logging
import re
import unittest

from charmscaler_basetest import BaseTest

log = logging.getLogger(__name__)


class TestCharm(BaseTest, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass("charmscaler")

    def test_restricted(self):
        self.d.configure("charmscaler", {
            "scaling_units_max": 5
        })
        try:
            self.d.sentry.wait_for_messages({
                "charmscaler":
                re.compile(r"Refusing to set a capacity limit max value")
            })
        except amulet.helpers.TimeoutError:
            message = "Never got restricted status message from charmscaler"
            amulet.raise_status(amulet.FAIL, msg=message)

        self._configure({
            "scaling_units_max": 4
        })


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("websocket").setLevel(logging.WARNING)
    logging.getLogger("websockets.protocol").setLevel(logging.WARNING)
    logging.getLogger("deployer").setLevel(logging.WARNING)
    unittest.main()
