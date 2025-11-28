import requests


def download_file(url, destination):
    """Downloads a file from a URL to a destination."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(destination, "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded {url} to {destination}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")


if __name__ == "__main__":
    vaneck_url = (
        "https://www.vaneck.com/de/de/investments/defense-etf/downloads/holdings/"
    )
    vaneck_dest = "tests/fixtures/vaneck_holdings.xlsx"
    download_file(vaneck_url, vaneck_dest)

    ishares_url = "https://www.ishares.com/de/privatanleger/de/produkte/251882/fund/1478358465952.ajax?fileType=csv&fileName=IWDA_holdings&dataType=fund"
    ishares_dest = "tests/fixtures/ishares_holdings.csv"
    download_file(ishares_url, ishares_dest)

    xtrackers_url = "https://etf.dws.com/etfdata/export/DEU/DEU/csv/product/constituent/IE00B1CD3B44/"
    xtrackers_dest = "tests/fixtures/xtrackers_holdings.csv"
    download_file(xtrackers_url, xtrackers_dest)
