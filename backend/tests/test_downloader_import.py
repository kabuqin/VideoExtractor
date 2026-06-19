from app.services.downloader import YtDlpDownloader


def test_downloader_can_be_constructed() -> None:
    downloader = YtDlpDownloader()

    assert downloader is not None

