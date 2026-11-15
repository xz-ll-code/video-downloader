"""
doc_convert.py
PDF ↔ Word 双向转换工具（交互式）。

依赖安装（建议用清华源）：
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pdf2docx docx2pdf
    Windows 原生方案另需：
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywin32

Word 转 PDF 引擎选择：
    · 默认：docx2pdf → LibreOffice
    · prefer_native=True（仅 Windows）：Word COM → docx2pdf → LibreOffice
    · docx2pdf 在 Windows/macOS 下依赖本机 Word，Linux 下依赖 LibreOffice；
      LibreOffice 无头模式不依赖 Word，作为最终兜底。
    · 未安装 Word 时请安装 LibreOffice，脚本会自动回退。
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

# ---------- PDF → Word ----------

def pdf_to_word(
    pdf_path: str,
    docx_path: str = None,
    start: int = 0,
    end: int = None,
    password: str = None,
) -> str:
    """PDF 转 Word，保留文字、表格、图片和基础排版。仅对文字型 PDF 有效。"""
    try:
        from pdf2docx import Converter
    except ImportError as e:
        raise ImportError(
            "未安装 pdf2docx，请运行：pip install pdf2docx"
        ) from e

    pdf_path = str(Path(pdf_path).resolve())
    if docx_path is None:
        docx_path = str(Path(pdf_path).with_suffix(".docx"))

    cv = Converter(pdf_path, password=password) if password else Converter(pdf_path)
    try:
        cv.convert(docx_path, start=start, end=end)
    finally:
        cv.close()
    return docx_path


# ---------- Word → PDF：引擎一，本机 Word COM ----------

def _word_to_pdf_win32(docx_path: str, pdf_path: str) -> str:
    """Windows 原生方案，调用本机 Microsoft Word COM 接口。"""
    try:
        import win32com.client
    except ImportError as e:
        raise ImportError(
            "未安装 pywin32，请运行：pip install pywin32"
        ) from e

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = None
    try:
        doc = word.Documents.Open(
            os.path.abspath(docx_path), ReadOnly=True, Format=16
        )
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        word.Quit()
    return pdf_path


# ---------- Word → PDF：引擎二，docx2pdf ----------

def _word_to_pdf_docx2pdf(docx_path: str, pdf_path: str) -> str:
    """docx2pdf 方案。Windows 下依赖本机 Word；macOS/Linux 依赖 LibreOffice。"""
    try:
        from docx2pdf import convert
    except ImportError as e:
        raise ImportError(
            "未安装 docx2pdf，请运行：pip install docx2pdf"
        ) from e

    convert(docx_path, pdf_path)
    return pdf_path


# ---------- Word → PDF：引擎三，LibreOffice 无头模式 ----------

def _find_soffice():
    """查找 LibreOffice 的 soffice 可执行文件，找不到返回 None。"""
    if platform.system() == "Windows":
        candidates = [
            r"E:\LibreOffice\program\soffice.exe",              # ← 你的实际路径
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif platform.system() == "Darwin":
        candidates = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
    else:
        candidates = [
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "/opt/libreoffice/program/soffice",
        ]

    for c in candidates:
        if Path(c).exists():
            return c

    return shutil.which("soffice") or shutil.which("libreoffice")

def _word_to_pdf_libreoffice(docx_path: str, pdf_path: str) -> str:
    """通过 LibreOffice 无头模式转换，完全不依赖 Microsoft Word。"""
    soffice = _find_soffice()
    if not soffice:
        raise FileNotFoundError(
            "未找到 LibreOffice。请安装 LibreOffice 后重试"
            "（Windows 默认路径：C:\\Program Files\\LibreOffice\\program\\soffice.exe）。"
        )

    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_dir = pdf_path.parent
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # 用临时用户配置目录，避免与已运行的 LibreOffice 实例冲突导致卡住
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile_dir:
        profile_url = "file:///" + profile_dir.replace(os.sep, "/").lstrip("/")
        cmd = [
            soffice,
            f"-env:UserInstallation={profile_url}",
            "--headless",
            "--norestore",
            "--convert-to", "pdf",
            "--outdir", str(pdf_dir),
            str(docx_path),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180
        )

    produced = pdf_dir / (docx_path.stem + ".pdf")
    if not produced.exists():
        raise RuntimeError(
            "LibreOffice 转换失败。\n"
            f"返回码: {result.returncode}\n"
            f"标准输出: {result.stdout}\n"
            f"标准错误: {result.stderr}"
        )

    # LibreOffice 输出文件名固定为源文件名，若目标名不同则重命名
    if produced != pdf_path:
        os.replace(produced, pdf_path)
    return str(pdf_path)


# ---------- Word → PDF：统一入口 ----------

def word_to_pdf(
    docx_path: str,
    pdf_path: str = None,
    prefer_native: bool = False,
) -> str:
    """
    Word 转 PDF，按引擎优先级依次尝试，全部失败才抛异常。

    prefer_native=False（默认）：docx2pdf → LibreOffice
    prefer_native=True：本机 Word COM → docx2pdf → LibreOffice（仅 Windows）
    """
    docx_path = str(Path(docx_path).resolve())
    if pdf_path is None:
        pdf_path = str(Path(docx_path).with_suffix(".pdf"))

    errors = []

    if prefer_native and platform.system() == "Windows":
        try:
            return _word_to_pdf_win32(docx_path, pdf_path)
        except Exception as e:
            errors.append(f"本机 Word COM 方案失败：{e}")

    try:
        return _word_to_pdf_docx2pdf(docx_path, pdf_path)
    except Exception as e:
        errors.append(f"docx2pdf 方案失败：{e}")

    try:
        return _word_to_pdf_libreoffice(docx_path, pdf_path)
    except Exception as e:
        errors.append(f"LibreOffice 方案失败：{e}")

    raise RuntimeError(
        "所有 Word 转 PDF 方案均失败：\n  " + "\n  ".join(errors)
    )


# ---------- 批量入口 ----------

def batch_convert(
    input_dir: str,
    output_dir: str,
    direction: str,
    max_workers: int = 4,
):
    """批量转换。direction: 'pdf2word' 或 'word2pdf'"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if direction == "pdf2word":
        files = list(input_dir.glob("*.pdf"))
        func = lambda p: pdf_to_word(str(p), str(output_dir / f"{p.stem}.docx"))
    elif direction == "word2pdf":
        files = [
            p for p in input_dir.iterdir()
            if p.suffix.lower() in (".doc", ".docx")
        ]
        # Word COM / LibreOffice 均不适合并发，强制单线程
        max_workers = 1
        func = lambda p: word_to_pdf(str(p), str(output_dir / f"{p.stem}.pdf"))
    else:
        raise ValueError("direction 必须是 'pdf2word' 或 'word2pdf'")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, p): p for p in files}
        for future in as_completed(futures):
            src = futures[future]
            try:
                results.append((src.name, "OK", future.result()))
            except Exception as e:
                results.append((src.name, f"FAIL: {e}", None))
    return results


# ---------- 交互式主程序 ----------

def _clean_path(p: str) -> str:
    """去掉首尾空白和拖拽文件时带上的引号。"""
    return os.path.expanduser(p.strip().strip('"').strip("'"))


def _guess_direction(path: Path):
    """根据文件/目录内容判断转换方向，返回 'pdf2word' / 'word2pdf' / None。"""
    if path.is_file():
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "pdf2word"
        if suffix in (".doc", ".docx"):
            return "word2pdf"
        return None

    pdfs = list(path.glob("*.pdf"))
    words = [p for p in path.iterdir() if p.suffix.lower() in (".doc", ".docx")]
    if pdfs and not words:
        return "pdf2word"
    if words and not pdfs:
        return "word2pdf"
    if pdfs and words:
        print("目录中同时包含 PDF 和 Word 文件，请选择转换方向：")
        print("  1) PDF → Word")
        print("  2) Word → PDF")
        choice = input("请输入 1 或 2（直接回车默认 1）：").strip() or "1"
        return "pdf2word" if choice == "1" else "word2pdf"
    return None


def main():
    print("=" * 56)
    print("PDF ↔ Word 双向转换工具")
    print("=" * 56)

    # 1. 询问源路径
    src_input = input("请输入要转换的文件或文件夹路径：").strip()
    src_path = Path(_clean_path(src_input))
    if not src_input or not src_path.exists():
        print(f"路径不存在或为空：{src_path}")
        return

    # 2. 判断转换方向
    direction = _guess_direction(src_path)
    if direction is None:
        print("没有找到可转换的 .pdf / .doc / .docx 文件。")
        return

    # 3. 询问存放路径，默认与源文件同目录
    default_out = src_path.parent if src_path.is_file() else src_path
    out_input = input(
        f"请输入存放路径（直接回车默认：{default_out}）："
    ).strip()
    out_dir = Path(_clean_path(out_input)) if out_input else default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    dir_label = "PDF → Word" if direction == "pdf2word" else "Word → PDF"
    print(f"\n转换方向：{dir_label}")
    print(f"输出目录：{out_dir}\n")

    # 4. 执行转换
    try:
        if src_path.is_file():
            if direction == "pdf2word":
                out_file = out_dir / f"{src_path.stem}.docx"
                print(f"正在转换：{src_path.name} → {out_file.name}")
                pdf_to_word(str(src_path), str(out_file))
            else:
                out_file = out_dir / f"{src_path.stem}.pdf"
                print(f"正在转换：{src_path.name} → {out_file.name}")
                word_to_pdf(str(src_path), str(out_file))
            print(f"完成：{out_file}")
        else:
            results = batch_convert(str(src_path), str(out_dir), direction)
            ok = sum(1 for _, status, _ in results if status == "OK")
            fail = len(results) - ok
            print(f"\n完成：成功 {ok} 个，失败 {fail} 个。")
            for name, status, out in results:
                line = f"  {name}: {status}"
                if out:
                    line += f" → {out}"
                print(line)
    except ImportError as e:
        print(f"\n缺少依赖：{e}")
        print(
            "请先执行：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "
            "pdf2docx docx2pdf pywin32"
        )
    except Exception as e:
        print(f"\n转换失败：{e}")


if __name__ == "__main__":
    main()