import asyncio
from playwright.async_api import async_playwright
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool
import os
import argparse
import logging

from config import Config
from file_processor import read_pickle, dump_json, prepare_path
from visualizer import draw_bbox


config = Config()
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', 
    datefmt='%d-%b-%y %H:%M:%S', 
    handlers=[logging.FileHandler('logs.log')]
)


async def get_elements_tree_structure(url, path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        
        await page.wait_for_load_state('load')
        page_size = await page.evaluate('''() => {
            return {
                width: document.documentElement.scrollWidth,
                height: document.documentElement.scrollHeight
            };
        }''')
        await page.set_viewport_size(page_size)
        
        await page.wait_for_load_state('load')
        
        elements_info = await page.evaluate('''() => {
            function hasVisibleText(text) {
                // 使用正则表达式检查文本是否包含非空白字符
                return /[\x21-\x7E]/.test(text);
            }
            function getElementInfo(node, path) {
                if (node.nodeType !== 1 && node.nodeType !== 3 || node.tagName && (node.tagName.toLowerCase() === 'script' || node.tagName.toLowerCase() === 'noscript')) {
                    return null;
                }
                let info = {};
                if (node.nodeType === 3) { // Text node
                    if (!hasVisibleText(node.nodeValue)) { // Exclude text nodes which only contain whitespace
                        return null;
                    }
                    if (!node.nodeValue.trim()) { // Exclude text nodes which only contain whitespace
                        return null;
                    }
                    // Get bounding box for text node using Range
                    var range = document.createRange();
                    range.selectNode(node);
                    var rect = range.getBoundingClientRect();
                    info = {
                        type: "text",
                        textContent: node.nodeValue.trim(),
                        xpath: path,
                        boxInfo: {
                            top: rect.top,
                            left: rect.left,
                            width: rect.width,
                            height: rect.height
                        }
                    };
                } else if (node.nodeType === 1) { // Element node
                    let rect = node.getBoundingClientRect();
                    info = {
                        type: "element",
                        tagName: node.tagName.toLowerCase(),
                        xpath: path,
                        boxInfo: {
                            top: rect.top,
                            left: rect.left,
                            width: rect.width,
                            height: rect.height
                        }
                    };
                    if (node.tagName.toLowerCase() === "img") {
                        info.src = node.src;
                        info.alt = node.alt;
                    }
                }
                let children = [];
                for (let i = 0; i < node.childNodes.length; i++) {
                    let childNode = node.childNodes[i];
                    let childInfo = getElementInfo(childNode, `${path}/node()[${i + 1}]`);
                    if (childInfo) {
                        children.push(childInfo);
                    }
                }
                if (children.length > 0) {
                    info.children = children;
                }
                return info;
            }
            return getElementInfo(document.body, "/html/body");
        }''')

        await page.screenshot(path=path, full_page=True)
        await browser.close()
        return elements_info


def process_url(args):
    idx, config, url = args
    logging.info(f"Processing {url}")
    if url.endswith('.pdf'):
        logging.error(f"PDF file found at index {idx}")
        return None
    try:
        url_name = str(idx)
        visible_elements_info = asyncio.run(get_elements_tree_structure(url, os.path.join('screenshots', url_name + '.png')))
        if visible_elements_info is not None:
            dump_json(visible_elements_info, os.path.join(config.annotations, url_name + '.json'))
            bbox_img = draw_bbox(Image.open(os.path.join(config.screenshots, url_name + '.png')), visible_elements_info)
            bbox_img.save(os.path.join(config.bbox_path, url_name + '.png'))
            logging.info(f"Processed {url}")
        else:
            logging.error(f"Error processing {url}, no visible elements found")
    except Exception as e:
        logging.error(f"Error: {str(e)}")


def get_args():
    parser = argparse.ArgumentParser()
    base_config = Config()
    parser.add_argument('--processes', type=int, default=base_config.processes)
    parser.add_argument('--url_list', type=str, default=base_config.url_list)
    parser.add_argument('--bbox_path', type=str, default=base_config.bbox_path)
    parser.add_argument('--screenshots', type=str, default=base_config.screenshots)
    parser.add_argument('--annotations', type=str, default=base_config.annotations)
    return parser.parse_args()


def main():
    args = get_args()
    config = Config(processes=args.processes, url_list=args.url_list, bbox_path=args.bbox_path, screenshots=args.screenshots, annotations=args.annotations)
    prepare_path(config)

    url_list = []
    if config.url_list == 'dummy':
        logging.info("Using dummy urls")
        url_list = ['https://www.example.com'] * 8
    elif os.path.exists(config.url_list):
        logging.info(f"Reading urls from {config.url_list}")
        url_list = read_pickle(config.url_list)
    else:
        logging.error(f"File not found: {config.url_list}")
        return

    if not url_list:
        logging.error("No urls found in the list")
        return

    logging.info(f"Processing {len(url_list)} urls with {config.processes} processes")
    with Pool(processes=config.processes) as pool:
        tasks = [(i, config, url) for i, url in enumerate(url_list)]
        for _ in tqdm(pool.imap_unordered(process_url, tasks), total=len(tasks)):
            pass


if __name__ == '__main__':
    main()
    logging.info("Done")
