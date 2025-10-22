"""
Dropbox Helper Module

This module provides utilities for uploading, downloading, and managing files in Dropbox.

Usage as a module:
    from campaign_automation.helper.dropbox_helper import DropboxSync

    # Initialize sync
    sync = DropboxSync()

    # Download input folder from Dropbox
    sync.download_folder('/input', './input')

    # Upload output folder to Dropbox
    sync.upload_folder('./output', '/output')

Usage for testing:
    python -m campaign_automation.helper.dropbox_helper

Setup:
    1. Install dependencies:
        pip install dropbox

    2. Add your Dropbox access token to credentials.json:
        {
          "dropbox": {
            "access_token": "your-dropbox-access-token"
          }
        }

    3. Get access token from:
        https://www.dropbox.com/developers/apps
"""

import os
from pathlib import Path
from typing import Optional
import dropbox
from dropbox.exceptions import ApiError, AuthError

from ..credentials import get_dropbox_access_token


class DropboxSync:
    """Handles syncing folders with Dropbox."""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Dropbox connection.

        Args:
            access_token: Optional Dropbox access token. If not provided, will use credentials.json
        """
        self.access_token = access_token or get_dropbox_access_token()

        if not self.access_token:
            raise ValueError("No Dropbox access token found. Please configure credentials.json")

        # Connect to Dropbox
        self.dbx = dropbox.Dropbox(self.access_token)

        # Verify connection
        try:
            account = self.dbx.users_get_current_account()
            print(f"[OK] Connected to Dropbox as: {account.name.display_name}")
        except AuthError as err:
            raise ValueError(f"Authentication error: {err}")

    def download_folder(self, remote_path: str, local_path: str, verbose: bool = True) -> int:
        """
        Download entire folder from Dropbox to local filesystem.

        Args:
            remote_path: Path in Dropbox (e.g., '/input')
            local_path: Local directory path (e.g., './input')
            verbose: Print progress messages

        Returns:
            Number of files downloaded
        """
        local_path = Path(local_path)
        local_path.mkdir(parents=True, exist_ok=True)

        files_downloaded = 0

        try:
            if verbose:
                print(f"\n[DOWNLOAD] From Dropbox: {remote_path} -> {local_path}")

            # List all files in the remote folder recursively
            result = self.dbx.files_list_folder(remote_path, recursive=True)

            # Process all entries
            while True:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        # Calculate local file path
                        relative_path = entry.path_display[len(remote_path):].lstrip('/')
                        local_file = local_path / relative_path

                        # Create parent directories if needed
                        local_file.parent.mkdir(parents=True, exist_ok=True)

                        # Download file
                        if verbose:
                            print(f"  <- {entry.path_display}")

                        metadata, response = self.dbx.files_download(entry.path_display)
                        local_file.write_bytes(response.content)

                        files_downloaded += 1

                # Check if there are more entries
                if not result.has_more:
                    break
                result = self.dbx.files_list_folder_continue(result.cursor)

            if verbose:
                print(f"[OK] Downloaded {files_downloaded} file(s)\n")

            return files_downloaded

        except ApiError as err:
            if err.error.is_path() and err.error.get_path().is_not_found():
                if verbose:
                    print(f"[WARNING] Remote folder not found: {remote_path}")
                return 0
            raise

    def upload_folder(self, local_path: str, remote_path: str, verbose: bool = True) -> int:
        """
        Upload entire folder from local filesystem to Dropbox.

        Args:
            local_path: Local directory path (e.g., './output')
            remote_path: Path in Dropbox (e.g., '/output')
            verbose: Print progress messages

        Returns:
            Number of files uploaded
        """
        local_path = Path(local_path)

        if not local_path.exists():
            if verbose:
                print(f"[WARNING] Local folder not found: {local_path}")
            return 0

        files_uploaded = 0

        try:
            if verbose:
                print(f"\n[UPLOAD] To Dropbox: {local_path} -> {remote_path}")

            # Walk through all files in local folder
            for local_file in local_path.rglob('*'):
                if local_file.is_file():
                    # Calculate relative path and remote file path
                    relative_path = local_file.relative_to(local_path)
                    remote_file = f"{remote_path}/{relative_path.as_posix()}"

                    if verbose:
                        print(f"  -> {remote_file}")

                    # Upload file (overwrite if exists)
                    with open(local_file, 'rb') as f:
                        self.dbx.files_upload(
                            f.read(),
                            remote_file,
                            mode=dropbox.files.WriteMode('overwrite')
                        )

                    files_uploaded += 1

            if verbose:
                print(f"[OK] Uploaded {files_uploaded} file(s)\n")

            return files_uploaded

        except ApiError as err:
            raise RuntimeError(f"Failed to upload folder: {err}")

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a single file from Dropbox.

        Args:
            remote_path: Path in Dropbox (e.g., '/input/campaigns/campaign.yaml')
            local_path: Local file path

        Returns:
            True if successful, False otherwise
        """
        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            metadata, response = self.dbx.files_download(remote_path)
            local_path.write_bytes(response.content)

            return True

        except ApiError as err:
            if err.error.is_path() and err.error.get_path().is_not_found():
                print(f"[WARNING] File not found in Dropbox: {remote_path}")
            else:
                print(f"[ERROR] Download failed: {err}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a single file to Dropbox.

        Args:
            local_path: Local file path
            remote_path: Path in Dropbox (e.g., '/output/report.md')

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(local_path, 'rb') as f:
                self.dbx.files_upload(
                    f.read(),
                    remote_path,
                    mode=dropbox.files.WriteMode('overwrite')
                )
            return True

        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False


# Module-level test code
if __name__ == "__main__":
    print("=" * 70)
    print("DROPBOX SYNC TEST")
    print("=" * 70)
    print()

    try:
        # Initialize sync
        sync = DropboxSync()

        # Test: Upload a test file
        print("Creating test file...")
        test_file = "test_dropbox.txt"
        with open(test_file, "w") as f:
            f.write("Hello Dropbox! This is a test upload from Python.\n")

        print("Uploading test file...")
        success = sync.upload_file(test_file, f"/{test_file}")

        if success:
            print(f"[OK] Test file uploaded successfully to /{test_file}")
        else:
            print("[ERROR] Test file upload failed")

        # Clean up local test file
        os.remove(test_file)
        print(f"[INFO] Removed local test file")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
