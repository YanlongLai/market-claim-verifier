"""Restore a hash-verified recorded SEC snapshot into a new cache, offline."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def restore(record_dir: Path, cache_dir: Path):
    if cache_dir.exists():
        raise ValueError('destination already exists; choose a new cache')
    manifest=json.loads((record_dir/'manifest.json').read_text())
    if manifest.get('errors'):
        raise ValueError('snapshot has recorded fetch errors')
    validated=[]
    for item in manifest['files']:
        name=item['file'];archive=item['archive']
        if Path(name).name!=name or Path(archive).parts!=('snapshots',name+'.gz'):
            raise ValueError('invalid snapshot path')
        raw=gzip.decompress((record_dir/archive).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ValueError('snapshot hash mismatch')
        json.loads(raw)
        validated.append((item,raw))
    cache_dir.mkdir(parents=True)
    for item,raw in validated:
        path=cache_dir/item['file'];path.write_bytes(raw)
        path.with_name(path.name+'.meta.json').write_text(json.dumps({k:item[k] for k in ('url','fetched_at','sha256')},indent=2)+'\n')
    return len(validated)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record_dir',type=Path)
    parser.add_argument('cache_dir',type=Path)
    args=parser.parse_args()
    print(f'Restored {restore(args.record_dir,args.cache_dir)} verified SEC files')


if __name__=='__main__':main()
