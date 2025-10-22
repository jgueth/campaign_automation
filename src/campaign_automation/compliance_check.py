"""
Logo Compliance Checker using OpenCV

This module verifies that brand logos are present in final campaign images
using feature-based detection to handle rotation, scaling, and positioning.

Uses ORB (Oriented FAST and Rotated BRIEF) feature detection which is:
- Fast and efficient
- Rotation invariant
- Scale invariant
- Free to use (no patent restrictions)

Usage:
    from campaign_automation.compliance_check import check_logo_in_image, check_campaign_compliance

    # Single image check
    result = check_logo_in_image(
        campaign_image_path='output/campaign.png',
        logo_path='input/assets/logo.png'
    )

    # Full campaign check
    stats = check_campaign_compliance(campaign_file='holiday_campaign.yaml')
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml


def check_logo_in_image(
    campaign_image_path: str,
    logo_path: str,
    min_match_count: int = 10,
    good_match_threshold: float = 0.75
) -> Dict[str, Any]:
    """
    Check if a logo is present in a campaign image using feature matching.

    This uses ORB feature detection which is robust to:
    - Rotation (logo can be at any angle)
    - Scale changes (logo can be larger/smaller)
    - Position (logo can be anywhere in image)

    Args:
        campaign_image_path: Path to the campaign image to check
        logo_path: Path to the logo image to find
        min_match_count: Minimum number of feature matches to consider logo found (default: 10)
        good_match_threshold: Ratio threshold for filtering good matches (default: 0.75)

    Returns:
        dict with:
            - found (bool): Whether logo was detected
            - match_count (int): Number of good feature matches found
            - confidence (float): Confidence score (0.0 - 1.0)
            - location (tuple): (x, y, width, height) of detected logo, or None
            - error (str): Error message if check failed, or None
    """
    try:
        # Load images
        campaign_img_path = Path(campaign_image_path)
        logo_img_path = Path(logo_path)

        if not campaign_img_path.exists():
            return {
                'found': False,
                'match_count': 0,
                'confidence': 0.0,
                'location': None,
                'error': f'Campaign image not found: {campaign_image_path}'
            }

        if not logo_img_path.exists():
            return {
                'found': False,
                'match_count': 0,
                'confidence': 0.0,
                'location': None,
                'error': f'Logo image not found: {logo_path}'
            }

        # Read images
        campaign_img = cv2.imread(str(campaign_img_path))
        logo_img = cv2.imread(str(logo_img_path))

        if campaign_img is None:
            return {
                'found': False,
                'match_count': 0,
                'confidence': 0.0,
                'location': None,
                'error': f'Could not read campaign image: {campaign_image_path}'
            }

        if logo_img is None:
            return {
                'found': False,
                'match_count': 0,
                'confidence': 0.0,
                'location': None,
                'error': f'Could not read logo image: {logo_path}'
            }

        # Convert to grayscale for feature detection
        campaign_gray = cv2.cvtColor(campaign_img, cv2.COLOR_BGR2GRAY)
        logo_gray = cv2.cvtColor(logo_img, cv2.COLOR_BGR2GRAY)

        # Initialize ORB detector
        # ORB is rotation-invariant and scale-invariant
        orb = cv2.ORB_create(nfeatures=1000)

        # Detect keypoints and compute descriptors
        kp1, des1 = orb.detectAndCompute(logo_gray, None)
        kp2, des2 = orb.detectAndCompute(campaign_gray, None)

        # Check if enough features were found
        if des1 is None or des2 is None:
            return {
                'found': False,
                'match_count': 0,
                'confidence': 0.0,
                'location': None,
                'error': 'Not enough features detected in images'
            }

        # Create BFMatcher (Brute Force Matcher)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # Match descriptors using KNN (K-Nearest Neighbors)
        matches = bf.knnMatch(des1, des2, k=2)

        # Apply ratio test to filter good matches (Lowe's ratio test)
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < good_match_threshold * n.distance:
                    good_matches.append(m)

        match_count = len(good_matches)

        # Calculate confidence score
        # Based on ratio of good matches to logo keypoints
        if len(kp1) > 0:
            confidence = min(match_count / len(kp1), 1.0)
        else:
            confidence = 0.0

        # Determine if logo is found
        logo_found = match_count >= min_match_count

        # Try to find logo location if enough matches
        location = None
        if logo_found and len(good_matches) >= 4:
            try:
                # Extract matched keypoints
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                # Find homography matrix (transformation from logo to campaign image)
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if M is not None:
                    # Get logo dimensions
                    h, w = logo_gray.shape

                    # Define corners of logo
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)

                    # Transform corners to campaign image coordinates
                    dst = cv2.perspectiveTransform(pts, M)

                    # Calculate bounding box
                    x_coords = dst[:, 0, 0]
                    y_coords = dst[:, 0, 1]

                    x = int(np.min(x_coords))
                    y = int(np.min(y_coords))
                    width = int(np.max(x_coords) - x)
                    height = int(np.max(y_coords) - y)

                    location = (x, y, width, height)
            except Exception as e:
                # Location detection failed, but we still found matches
                pass

        return {
            'found': logo_found,
            'match_count': match_count,
            'confidence': round(confidence, 3),
            'location': location,
            'error': None
        }

    except Exception as e:
        return {
            'found': False,
            'match_count': 0,
            'confidence': 0.0,
            'location': None,
            'error': f'Logo detection error: {str(e)}'
        }


def check_campaign_compliance(
    campaign_file: str = "holiday_campaign.yaml",
    min_match_count: int = 10,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Check logo compliance for all generated campaign images.

    Verifies that each localized campaign image contains the correct product logo.

    Args:
        campaign_file: Path to campaign YAML file
        min_match_count: Minimum feature matches to consider logo present
        verbose: Print detailed progress messages

    Returns:
        dict with:
            - total_checked (int): Total images checked
            - passed (int): Images with logo detected
            - failed (int): Images without logo detected
            - errors (int): Images that couldn't be checked
            - results (list): Detailed results per image
    """
    if verbose:
        print("=" * 70)
        print("LOGO COMPLIANCE CHECK")
        print("=" * 70)
        print()

    # Load campaign YAML
    campaign_path = Path(campaign_file)
    if not campaign_path.is_absolute():
        if len(campaign_path.parts) == 1:
            campaign_path = Path("input/campaigns") / campaign_file

    if not campaign_path.exists():
        return {
            'total_checked': 0,
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'results': [],
            'error': f'Campaign file not found: {campaign_path}'
        }

    with open(campaign_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    campaign = data.get('campaign', {})
    products = data.get('products', [])

    campaign_id = campaign.get('id')
    markets = campaign.get('markets', [])
    aspect_ratios = data.get('creative', {}).get('aspect_ratios', [])

    if verbose:
        print(f"Campaign: {campaign_id}")
        print(f"Products: {len(products)}")
        print(f"Markets: {len(markets)}")
        print(f"Aspect Ratios: {len(aspect_ratios)}")
        print()

    # Track statistics
    total_checked = 0
    passed = 0
    failed = 0
    errors = 0
    results = []

    # Check each product × ratio × market combination
    for product in products:
        product_id = product.get('id')
        logo_filename = product.get('assets', {}).get('logo')

        if not logo_filename:
            if verbose:
                print(f"[SKIP] {product_id}: No logo specified in YAML")
            continue

        logo_path = f"input/assets/{logo_filename}"

        for aspect_ratio in aspect_ratios:
            for market in markets:
                market_id = market.get('market_id')

                # Path to localized campaign image
                image_filename = f"campaign_{product_id}_{market_id}_{aspect_ratio}.png"
                image_path = f"output/{campaign_id}/{product_id}/{aspect_ratio}/{market_id}/{image_filename}"

                if not Path(image_path).exists():
                    if verbose:
                        print(f"[SKIP] {product_id} | {aspect_ratio} | {market_id}: Image not found")
                    continue

                total_checked += 1

                if verbose:
                    print(f"Checking: {product_id} | {aspect_ratio} | {market_id}")

                # Perform logo detection
                result = check_logo_in_image(
                    campaign_image_path=image_path,
                    logo_path=logo_path,
                    min_match_count=min_match_count
                )

                # Store result
                result_entry = {
                    'product_id': product_id,
                    'aspect_ratio': aspect_ratio,
                    'market_id': market_id,
                    'image_path': image_path,
                    'logo_path': logo_path,
                    **result
                }
                results.append(result_entry)

                # Update statistics
                if result['error']:
                    errors += 1
                    if verbose:
                        print(f"  [ERROR] {result['error']}")
                elif result['found']:
                    passed += 1
                    if verbose:
                        confidence_pct = int(result['confidence'] * 100)
                        print(f"  [SUCCESS] Logo detected ({result['match_count']} matches, {confidence_pct}% confidence)")
                else:
                    failed += 1
                    if verbose:
                        print(f"  [WARNING] Logo NOT detected ({result['match_count']} matches, below threshold)")

                if verbose:
                    print()

    # Summary
    if verbose:
        print("=" * 70)
        print("COMPLIANCE SUMMARY")
        print("=" * 70)
        print(f"Total images checked: {total_checked}")
        print(f"[SUCCESS] Passed (logo detected): {passed}")
        print(f"[WARNING] Failed (logo missing): {failed}")
        if errors > 0:
            print(f"[ERROR] Errors: {errors}")

        if total_checked > 0:
            pass_rate = (passed / total_checked) * 100
            print(f"Pass rate: {pass_rate:.1f}%")
        print()

    return {
        'total_checked': total_checked,
        'passed': passed,
        'failed': failed,
        'errors': errors,
        'results': results
    }


if __name__ == "__main__":
    """Test the logo compliance checker."""
    import sys

    # Parse arguments
    campaign_file = sys.argv[1] if len(sys.argv) > 1 else "holiday_campaign.yaml"

    print(f"\nTesting Logo Compliance Checker")
    print(f"Campaign: {campaign_file}\n")

    try:
        stats = check_campaign_compliance(
            campaign_file=campaign_file,
            verbose=True
        )

        # Exit with error code if any checks failed
        if stats['failed'] > 0 or stats['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"[ERROR] Compliance check failed: {e}")
        sys.exit(1)
