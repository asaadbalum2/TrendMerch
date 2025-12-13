#!/usr/bin/env python3
"""
Cloud Uploader for TrendMerch
Uploads designs to GitHub Releases or ImgBB for permanent storage
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Optional


def upload_to_imgbb(image_path: str, api_key: str = None) -> Optional[dict]:
    """
    Upload image to ImgBB (free image hosting).
    Get free API key at: https://api.imgbb.com/
    """
    api_key = api_key or os.environ.get('IMGBB_API_KEY')
    
    if not api_key:
        print("⚠️ IMGBB_API_KEY not set. Skipping ImgBB upload.")
        return None
    
    url = "https://api.imgbb.com/1/upload"
    
    with open(image_path, 'rb') as f:
        import base64
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        'key': api_key,
        'image': image_data,
        'name': Path(image_path).stem,
    }
    
    try:
        response = requests.post(url, data=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            return {
                'url': data['data']['url'],
                'display_url': data['data']['display_url'],
                'delete_url': data['data']['delete_url'],
                'thumb_url': data['data']['thumb']['url'],
            }
    except Exception as e:
        print(f"❌ ImgBB upload failed: {e}")
    
    return None


def create_github_release(
    repo: str,
    tag: str,
    files: List[str],
    token: str = None,
    title: str = None,
    body: str = None
) -> Optional[dict]:
    """
    Create a GitHub release and upload files.
    
    Args:
        repo: Repository name (e.g., 'username/repo')
        tag: Release tag (e.g., 'designs-2024-01-15')
        files: List of file paths to upload
        token: GitHub token (or use GITHUB_TOKEN env var)
        title: Release title
        body: Release description
    """
    token = token or os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("⚠️ GITHUB_TOKEN not set. Skipping GitHub release.")
        return None
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    # Create release
    api_url = f"https://api.github.com/repos/{repo}/releases"
    
    release_data = {
        'tag_name': tag,
        'name': title or f"Designs - {tag}",
        'body': body or f"Auto-generated T-shirt designs from TrendMerch\n\nGenerated: {datetime.now().isoformat()}",
        'draft': False,
        'prerelease': False,
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=release_data, timeout=30)
        response.raise_for_status()
        release = response.json()
        
        upload_url = release['upload_url'].replace('{?name,label}', '')
        release_url = release['html_url']
        
        print(f"📦 Created release: {release_url}")
        
        # Upload files
        uploaded = []
        for file_path in files:
            if not os.path.exists(file_path):
                continue
                
            filename = os.path.basename(file_path)
            
            upload_headers = headers.copy()
            upload_headers['Content-Type'] = 'application/octet-stream'
            
            with open(file_path, 'rb') as f:
                file_response = requests.post(
                    f"{upload_url}?name={filename}",
                    headers=upload_headers,
                    data=f,
                    timeout=120
                )
                
                if file_response.status_code in [200, 201]:
                    asset = file_response.json()
                    uploaded.append({
                        'name': filename,
                        'url': asset['browser_download_url'],
                        'size': asset['size']
                    })
                    print(f"   ✅ Uploaded: {filename}")
                else:
                    print(f"   ❌ Failed: {filename}")
        
        return {
            'release_url': release_url,
            'tag': tag,
            'files': uploaded
        }
        
    except Exception as e:
        print(f"❌ GitHub release failed: {e}")
        return None


def upload_designs(design_paths: List[str], method: str = "github") -> dict:
    """
    Upload designs using the specified method.
    
    Args:
        design_paths: List of paths to design files
        method: 'github' or 'imgbb'
    
    Returns:
        dict with upload results
    """
    results = {
        'method': method,
        'uploaded': [],
        'failed': []
    }
    
    if not design_paths:
        print("No designs to upload.")
        return results
    
    print(f"\n📤 Uploading {len(design_paths)} design(s)...")
    
    if method == "imgbb":
        for path in design_paths:
            result = upload_to_imgbb(path)
            if result:
                results['uploaded'].append({
                    'file': path,
                    **result
                })
            else:
                results['failed'].append(path)
                
    elif method == "github":
        repo = os.environ.get('GITHUB_REPOSITORY', 'asaadbalum2/TrendMerch')
        tag = f"designs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        release = create_github_release(repo, tag, design_paths)
        
        if release:
            results['release'] = release
            results['uploaded'] = release['files']
        else:
            results['failed'] = design_paths
    
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Uploaded: {len(results['uploaded'])}")
    print(f"   ❌ Failed: {len(results['failed'])}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cloud_uploader.py <file1> [file2] ...")
        sys.exit(1)
    
    files = sys.argv[1:]
    result = upload_designs(files, method="github")
    print(json.dumps(result, indent=2))

