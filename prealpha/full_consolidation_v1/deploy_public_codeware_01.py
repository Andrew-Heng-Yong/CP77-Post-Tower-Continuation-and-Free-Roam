"""Install or restore the untouched public Codeware 1.21.1 global script."""

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parent.parent
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
archive = workspace / 'diagnostics/core_updates_20261025_01/downloads/Codeware-1.21.1.zip'
backup = workspace / 'recovery/public_codeware_v1_21_1_01'
relative = Path('red4ext/plugins/Codeware/Scripts/Codeware.Global.reds')
target = game / relative
old_sha = '9736FEBC39BF88AD920068737BA6BBD0BC78F39D3E785FB629558E39AAAF990B'
new_sha = '83CEBFDAF60443608ACD211B1AC6253AE6C67295BAB97275B4961506EB878A76'
zip_sha = '7CEA413C39BBA6DEA15DE558E95BB0E04F63AF3D3CB35C6D854ED65382FD41A7'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def read(path):
    return path.read_bytes() if path.is_file() else None


def game_closed():
    dword = ctypes.c_ulong
    ids = (dword * 8192)()
    used = dword()
    psapi = ctypes.WinDLL('psapi')
    kernel = ctypes.WinDLL('kernel32')
    psapi.EnumProcesses.argtypes = (ctypes.POINTER(dword), dword, ctypes.POINTER(dword))
    psapi.EnumProcesses.restype = ctypes.c_int
    kernel.OpenProcess.argtypes = (dword, ctypes.c_int, dword)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = (ctypes.c_void_p, dword, ctypes.c_wchar_p, ctypes.POINTER(dword))
    kernel.QueryFullProcessImageNameW.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    assert psapi.EnumProcesses(ids, ctypes.sizeof(ids), ctypes.byref(used)), 'Cannot inspect running processes'
    assert used.value < ctypes.sizeof(ids), 'Process list truncated'
    forbidden = {'cyberpunk2077.exe', 'redprelauncher.exe'}
    for pid in ids[:used.value // ctypes.sizeof(dword)]:
        if not pid:
            continue
        handle = kernel.OpenProcess(0x1000, 0, pid)
        if not handle:
            continue
        try:
            name = ctypes.create_unicode_buffer(32768)
            length = dword(len(name))
            if kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(length)):
                assert Path(name.value).name.lower() not in forbidden, 'Close Cyberpunk 2077 and REDprelauncher first'
        finally:
            kernel.CloseHandle(handle)


def package():
    assert sha(archive.read_bytes()) == zip_sha
    rows = []
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            name = entry.filename.replace('\\', '/')
            assert not name.startswith('/') and '..' not in Path(name).parts
            rows.append((name, bundle.read(entry)))
    assert len(rows) == 9 and len({name.lower() for name, _ in rows}) == 9
    assert [sha(data) for name, data in rows if name == relative.as_posix()] == [new_sha]
    return rows


def package_matches(rows, allow_old):
    for name, data in rows:
        installed = read(game / name)
        expected = old_sha if allow_old and name == relative.as_posix() else sha(data)
        assert installed is not None and sha(installed) == expected, 'Installed Codeware drift: ' + name


def receipt(status):
    row = {
        'status': status,
        'version': '1.21.1',
        'public_zip_sha256': zip_sha,
        'target': str(target),
        'before_sha256': old_sha,
        'public_sha256': new_sha,
        'game_launched': False,
        'save_edits': 0,
        'live_result': 'pending',
    }
    (backup / 'receipt.json').write_text(json.dumps(row, indent=2) + '\n', encoding='utf-8')


def swap(data):
    temp = target.with_name(target.name + '.ptfr_swap_tmp')
    assert not temp.exists(), 'Unexpected Codeware swap temp file'
    temp.write_bytes(data)
    assert sha(temp.read_bytes()) == sha(data)
    try:
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()
    assert sha(target.read_bytes()) == sha(data)


def main(action):
    assert game.resolve() in target.resolve().parents
    assert workspace.resolve() in backup.resolve().parents
    rows = package()
    game_closed()
    saved = backup / 'Codeware.Global.reds.before'
    public = backup / 'Codeware.Global.reds.public'
    if action in ('Validate', 'Install'):
        assert not backup.exists(), 'Codeware swap backup already exists'
        package_matches(rows, allow_old=True)
        if action == 'Validate':
            return {'status': 'READY', 'package_files': len(rows), 'files_to_replace': 1}
        backup.mkdir(parents=True)
        shutil.copyfile(target, saved)
        assert sha(saved.read_bytes()) == old_sha
        public.write_bytes(next(data for name, data in rows if name == relative.as_posix()))
        assert sha(public.read_bytes()) == new_sha
        receipt('BACKED_UP_READY_TO_SWAP')
        swap(public.read_bytes())
        package_matches(rows, allow_old=False)
        receipt('PUBLIC_CODEWARE_1_21_1_INSTALLED_LIVE_PENDING')
        return {'status': 'PUBLIC_CODEWARE_1_21_1_INSTALLED_LIVE_PENDING', 'package_files': len(rows), 'files_replaced': 1}
    assert backup.is_dir() and sha(saved.read_bytes()) == old_sha and sha(public.read_bytes()) == new_sha
    if action in ('Verify', 'ValidateRollback'):
        package_matches(rows, allow_old=False)
        return {'status': 'VERIFIED' if action == 'Verify' else 'ROLLBACK_READY', 'package_files': len(rows)}
    assert action == 'Rollback'
    package_matches(rows, allow_old=False)
    swap(saved.read_bytes())
    package_matches(rows, allow_old=True)
    receipt('ROLLED_BACK_TO_LOCAL_PATCH')
    return {'status': 'ROLLED_BACK_TO_LOCAL_PATCH', 'files_restored': 1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('Validate', 'Install', 'Verify', 'ValidateRollback', 'Rollback'))
    print(json.dumps(main(parser.parse_args().action)))
