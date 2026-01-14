/**
 * ACTS Version Manager
 *
 * Handles dynamic version selection and PR build detection for ACTS documentation.
 * This file is auto-patched by deploy_docs.py to fix root detection.
 */

class ActsVersionManager {
  constructor() {
    this.siteRoot = null;
    this.prMetadata = null;
    console.log('[ACTS] Version manager initialized');
  }

  /**
   * Discover the docs root by looking for versions.json
   * @returns {Promise<string>} Path to docs root
   */
  async discoverDocsRoot() {
    const pathname = window.location.pathname;
    const cleanPath = pathname.replace(/^\/+|\/+$/g, '');
    const parts = cleanPath.split('/');
    const maxDepth = parts.length;

    // Try each level from current directory up to domain root
    // Look for versions.json which only exists at the true root
    for (let depth = 0; depth <= maxDepth; depth++) {
      const path = depth === 0 ? '.' : '../'.repeat(depth).slice(0, -1);

      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 500);

        const response = await fetch(`${path}/versions.json`, {
          method: 'HEAD',
          signal: controller.signal
        });

        clearTimeout(timeout);

        if (response.ok) {
          console.log(`[ACTS] Discovered docs root at: ${path}`);
          return path;
        }
      } catch (error) {
        // Continue searching
      }
    }

    console.warn('[ACTS] Could not discover docs root');
    return '.';
  }

  /**
   * Check for PR build by attempting to fetch pr.json
   * @returns {Promise<object|null>} PR metadata or null
   */
  async checkForPRBuild() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2000);

      const response = await fetch(`${this.siteRoot}/pr.json`, {
        cache: 'no-store',
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        console.log('[ACTS] No pr.json found - not a PR build');
        return null;
      }

      const data = await response.json();

      if (!data.pr || !data.url) {
        console.warn('[ACTS] Invalid pr.json structure');
        return null;
      }

      console.log('[ACTS] PR build detected:', data);
      return data;
    } catch (error) {
      if (error.name === 'AbortError') {
        console.warn('[ACTS] pr.json fetch timeout');
      }
      return null;
    }
  }

  /**
   * Render PR build banner at the top of #doc-content
   */
  renderPRBanner(metadata) {
    const docContent = document.querySelector('#doc-content');
    if (!docContent) {
      console.warn('[ACTS] Cannot render PR banner - #doc-content not found');
      return;
    }

    const banner = document.createElement('div');
    banner.id = 'acts-pr-banner';

    let content = `<strong>PR Build #${metadata.pr}</strong>`;
    if (metadata.branch) {
      content += ` from branch <code>${metadata.branch}</code>`;
    }
    if (metadata.title) {
      content += ` - ${metadata.title}`;
    }
    if (metadata.url) {
      content = `${content} (<a href="${metadata.url}" target="_blank" rel="noopener">View PR</a>)`;
    }

    banner.innerHTML = content;
    docContent.prepend(banner);
    console.log('[ACTS] PR banner rendered');
  }

  /**
   * Load external version-selector.js from site root
   */
  async loadExternalVersionSelector() {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = `${this.siteRoot}/version-selector.js`;

      const timeout = setTimeout(() => {
        console.warn('[ACTS] External version-selector.js timeout');
        script.remove();
        this.renderMinimalSelector();
        resolve(false);
      }, 5000);

      script.onload = () => {
        clearTimeout(timeout);

        if (typeof window.initVersionSelector === 'function') {
          try {
            console.log('[ACTS] External version-selector.js loaded');
            window.initVersionSelector({
              container: '#acts-version-selector',
              currentPath: window.location.pathname,
              siteRoot: this.siteRoot
            });
            resolve(true);
          } catch (error) {
            console.error('[ACTS] version-selector.js init failed:', error);
            this.renderMinimalSelector();
            resolve(false);
          }
        } else {
          console.warn('[ACTS] version-selector.js missing initVersionSelector');
          this.renderMinimalSelector();
          resolve(false);
        }
      };

      script.onerror = () => {
        clearTimeout(timeout);
        console.log('[ACTS] External version-selector.js not available');
        this.renderMinimalSelector();
        resolve(false);
      };

      document.head.appendChild(script);
    });
  }

  renderMinimalSelector() {
    const container = document.querySelector('#acts-version-selector');
    if (container) {
      container.remove();
    }
  }

  async init() {
    this.siteRoot = await this.discoverDocsRoot();
    console.log('[ACTS] Using docs root:', this.siteRoot);

    this.prMetadata = await this.checkForPRBuild();

    if (this.prMetadata) {
      this.renderPRBanner(this.prMetadata);
    } else {
      const sideNav = document.querySelector('#side-nav');
      if (sideNav) {
        const container = document.createElement('div');
        container.id = 'acts-version-selector';
        sideNav.prepend(container);
        await this.loadExternalVersionSelector();
      }
    }
  }
}

$(document).ready(function() {
  const versionManager = new ActsVersionManager();
  versionManager.init();
});
