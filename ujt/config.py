import configparser

# default values
CLEAR_CACHE_ON_STARTUP = True
REFRESH_TOPOLOGY_ON_STARTUP = True

AUTO_REFRESH_SLI = True
CLIENT_SLI_REFRESH_INTERVAL_MILLIS = 30 * 1000  # ms

REPORTING_SERVER_ADDRESS = "localhost:50051"


def load_config(config_path):
    if config_path is None:
        return

    config = configparser.ConfigParser()
    config.read(config_path)

    global CLEAR_CACHE_ON_STARTUP, REFRESH_TOPOLOGY_ON_STARTUP, AUTO_REFRESH_SLI, CLIENT_SLI_REFRESH_INTERVAL_MILLIS, REPORTING_SERVER_ADDRESS
    CLEAR_CACHE_ON_STARTUP = config["CACHE"].getboolean("CLEAR_CACHE_ON_STARTUP")
    REFRESH_TOPOLOGY_ON_STARTUP = config["CACHE"].getboolean(
        "REFRESH_TOPOLOGY_ON_STARTUP"
    )

    AUTO_REFRESH_SLI = config["SLIS"].getboolean("AUTO_REFRESH_SLI")
    CLIENT_SLI_REFRESH_INTERVAL_MILLIS = config["SLIS"].getint(
        "CLIENT_SLI_REFRESH_INTERVAL_MILLIS"
    )

    REPORTING_SERVER_ADDRESS = config["REPORTING_SERVER"]["REPORTING_SERVER_ADDRESS"]
