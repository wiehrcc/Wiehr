

(function() {
    'use strict';

    const CONFIG = {
        safetyMargin: 40,
        minSectionHeight: 200,
        transitionDuration: 200,
        scrollCooldown: 300,
        scrollThreshold: 30
    };

    let instances = [];

    class ViewportSections {
        constructor(container) {
            this.container = container;
            this.sections = [];
            this.currentIndex = 0;
            this.isTransitioning = false;
            this.lastScrollTime = 0;
            this.accumulatedDelta = 0;
            this.scrollTimeout = null;
            this.flipper = null;
            this.sectionsContainer = null;
            this.originalContent = null;
            this.boundHandleWheel = this.handleWheel.bind(this);
            this.boundHandleKeydown = this.handleKeydown.bind(this);
            this.boundHandleTouchStart = this.handleTouchStart.bind(this);
            this.boundHandleTouchMove = this.handleTouchMove.bind(this);
            this.boundHandleHashChange = this.handleHashChange.bind(this);
            this.touchStartY = 0;
            this.touchStartTime = 0;
            this.sectionAnchors = [];

            this.init();
        }

        init() {
            this.originalContent = this.container.innerHTML;
            this.sliceContent();
            this.generateAnchors();
            this.createNavigation();
            this.setupEventListeners();


            const initialIndex = this.getIndexFromHash();
            this.showSection(initialIndex);
            this.currentIndex = initialIndex;
            this.updateNavigation();


            this.updateHash(initialIndex);
        }

        generateAnchors() {
            this.sectionAnchors = this.sections.map((section, index) => {
                if (section.label) {

                    return section.label.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
                }
                return (index + 1).toString();
            });
        }

        getIndexFromHash() {
            const hash = window.location.hash.slice(1); 
            if (!hash) return 0;


            const index = this.sectionAnchors.findIndex(anchor => anchor === hash.toLowerCase());
            if (index !== -1) return index;


            const numIndex = parseInt(hash, 10) - 1;
            if (!isNaN(numIndex) && numIndex >= 0 && numIndex < this.sections.length) {
                return numIndex;
            }

            return 0;
        }

        updateHash(index) {
            const anchor = this.sectionAnchors[index];
            if (anchor) {
                const newHash = '#' + anchor;


                if (window.location.hash !== newHash) {
                    history.replaceState(null, '', newHash);
                }
            }
        }

        handleHashChange() {
            const targetIndex = this.getIndexFromHash();
            if (targetIndex !== this.currentIndex) {
                this.goToSection(targetIndex);
            }
        }

        getAvailableHeight() {
            const vh = window.innerHeight;

            const probe = document.createElement('div');
            probe.className = 'viewport-section-content';
            probe.style.visibility = 'hidden';
            probe.style.position = 'absolute';
            document.body.appendChild(probe);
            const style = window.getComputedStyle(probe);
            const reserved =
                (parseFloat(style.marginTop) || 0) +
                (parseFloat(style.marginBottom) || 0) +
                (parseFloat(style.paddingTop) || 0) +
                (parseFloat(style.paddingBottom) || 0) +
                (parseFloat(style.borderTopWidth) || 0) +
                (parseFloat(style.borderBottomWidth) || 0);
            document.body.removeChild(probe);
            return vh - reserved - CONFIG.safetyMargin;
        }

        getColumnGap() {
            const probe = document.createElement('div');
            probe.className = 'viewport-section-content';
            probe.style.cssText = 'visibility:hidden;position:absolute';
            document.body.appendChild(probe);
            const gap = parseFloat(window.getComputedStyle(probe).rowGap) || 0;
            document.body.removeChild(probe);
            return gap;
        }

        getContentWidth() {
            const probe = document.createElement('div');
            probe.className = 'viewport-section-content';
            probe.style.cssText = 'visibility:hidden;position:absolute';
            document.body.appendChild(probe);
            const style = window.getComputedStyle(probe);
            const inner = probe.clientWidth -
                (parseFloat(style.paddingLeft) || 0) -
                (parseFloat(style.paddingRight) || 0);
            document.body.removeChild(probe);
            return Math.max(160, Math.round(inner));
        }

        sliceContent() {
            const sourceElements = this.container.querySelectorAll('.legal-section, [data-viewport-item]');
            if (sourceElements.length === 0) return;

            const availableHeight = this.getAvailableHeight();
            const columnGap = this.getColumnGap();
            const contentWidth = this.getContentWidth();

            const measureHost = document.createElement('div');
            measureHost.className = 'viewport-section';
            measureHost.style.cssText =
                'position:absolute;left:-99999px;top:0;visibility:hidden;' +
                'display:block;height:auto;width:' + contentWidth + 'px;';

            const tempContainer = document.createElement('div');
            tempContainer.className = 'viewport-section-content';
            tempContainer.style.cssText =
                'width:100%;max-width:none;margin:0;padding:0;border:0;' +
                'max-height:none;overflow:visible;';

            measureHost.appendChild(tempContainer);
            document.body.appendChild(measureHost);

            let currentSection = {
                elements: [],
                height: 0,
                label: null,
                icon: null,
                sourceIndex: 0
            };
            let sectionIndex = 0;

            sourceElements.forEach((element, index) => {
                const clone = element.cloneNode(true);
                tempContainer.innerHTML = '';
                tempContainer.appendChild(clone);
                const elementHeight = tempContainer.offsetHeight +
                    (currentSection.elements.length ? columnGap : 0);

                const label = element.dataset.viewportLabel || null;
                const icon = element.dataset.viewportIcon || null;

                if (elementHeight > availableHeight) {
                    if (currentSection.elements.length > 0) {
                        currentSection.label = currentSection.label || label;
                        currentSection.icon = currentSection.icon || icon;
                        this.sections.push({ ...currentSection });
                        sectionIndex++;
                    }

                    const slicedSections = this.sliceLargeElement(element, availableHeight, tempContainer, label, icon);
                    slicedSections.forEach(sliced => {
                        this.sections.push({
                            elements: [sliced.html],
                            height: sliced.height,
                            label: label,
                            icon: icon,
                            sourceIndex: index,
                            isPartial: true,
                            partNumber: sliced.partNumber,
                            totalParts: sliced.totalParts
                        });
                        sectionIndex++;
                    });

                    currentSection = {
                        elements: [],
                        height: 0,
                        label: null,
                        icon: null,
                        sourceIndex: index + 1
                    };
                } else if (currentSection.height + elementHeight > availableHeight && currentSection.elements.length > 0) {
                    this.sections.push({ ...currentSection });
                    sectionIndex++;

                    currentSection = {
                        elements: [element.outerHTML],
                        height: elementHeight,
                        label: label,
                        icon: icon,
                        sourceIndex: index
                    };
                } else {
                    currentSection.elements.push(element.outerHTML);
                    currentSection.height += elementHeight;
                    if (!currentSection.label && label) currentSection.label = label;
                    if (!currentSection.icon && icon) currentSection.icon = icon;
                }
            });

            if (currentSection.elements.length > 0) {
                this.sections.push(currentSection);
            }

            document.body.removeChild(measureHost);
            this.renderSections();
        }

        sliceLargeElement(element, availableHeight, tempContainer, label, icon) {
            const result = [];
            const children = element.children;
            const header = element.querySelector('h2, h3');
            const headerHTML = header ? header.outerHTML : '';
            const headerHeight = header ? this.measureHeight(headerHTML, tempContainer) : 0;

            let currentPart = {
                html: '',
                height: 0
            };
            let partNumber = 1;
            let isFirstPart = true;

            if (header && headerHeight < availableHeight) {
                currentPart.html = headerHTML;
                currentPart.height = headerHeight;
            }

            Array.from(children).forEach((child, childIndex) => {
                if (header && childIndex === 0 && child === header) return;

                const childHTML = child.outerHTML;
                const childHeight = this.measureHeight(childHTML, tempContainer);

                if (childHeight > availableHeight) {
                    if (currentPart.html) {
                        result.push({
                            html: this.wrapPartialContent(element, currentPart.html, isFirstPart),
                            height: currentPart.height,
                            partNumber: partNumber++,
                            totalParts: 0
                        });
                        isFirstPart = false;
                    }

                    const textParts = this.sliceTextContent(child, availableHeight, tempContainer, element, isFirstPart);
                    textParts.forEach(part => {
                        result.push({
                            html: part.html,
                            height: part.height,
                            partNumber: partNumber++,
                            totalParts: 0
                        });
                        isFirstPart = false;
                    });

                    currentPart = { html: '', height: 0 };
                } else if (currentPart.height + childHeight > availableHeight) {
                    if (currentPart.html) {
                        result.push({
                            html: this.wrapPartialContent(element, currentPart.html, isFirstPart),
                            height: currentPart.height,
                            partNumber: partNumber++,
                            totalParts: 0
                        });
                        isFirstPart = false;
                    }
                    currentPart = {
                        html: childHTML,
                        height: childHeight
                    };
                } else {
                    currentPart.html += childHTML;
                    currentPart.height += childHeight;
                }
            });

            if (currentPart.html) {
                result.push({
                    html: this.wrapPartialContent(element, currentPart.html, isFirstPart),
                    height: currentPart.height,
                    partNumber: partNumber,
                    totalParts: 0
                });
            }

            const totalParts = result.length;
            result.forEach(part => {
                part.totalParts = totalParts;
            });

            return result;
        }

        sliceTextContent(element, availableHeight, tempContainer, parentElement, isFirst) {
            const result = [];
            const tagName = element.tagName.toLowerCase();

            if (tagName === 'ul' || tagName === 'ol') {
                const items = element.querySelectorAll('li');
                let currentItems = [];
                let currentHeight = 0;

                items.forEach(item => {
                    const itemHeight = this.measureHeight(`<${tagName}>${item.outerHTML}</${tagName}>`, tempContainer);

                    if (currentHeight + itemHeight > availableHeight && currentItems.length > 0) {
                        const listHTML = `<${tagName}>${currentItems.join('')}</${tagName}>`;
                        result.push({
                            html: this.wrapPartialContent(parentElement, listHTML, isFirst && result.length === 0),
                            height: currentHeight
                        });
                        currentItems = [];
                        currentHeight = 0;
                    }

                    currentItems.push(item.outerHTML);
                    currentHeight += itemHeight;
                });

                if (currentItems.length > 0) {
                    const listHTML = `<${tagName}>${currentItems.join('')}</${tagName}>`;
                    result.push({
                        html: this.wrapPartialContent(parentElement, listHTML, isFirst && result.length === 0),
                        height: currentHeight
                    });
                }
            } else {
                result.push({
                    html: this.wrapPartialContent(parentElement, element.outerHTML, isFirst),
                    height: this.measureHeight(element.outerHTML, tempContainer)
                });
            }

            return result;
        }

        wrapPartialContent(originalElement, content, includeHeader) {
            const classes = originalElement.className;

            return `<div class="${classes}">${content}</div>`;
        }

        measureHeight(html, tempContainer) {
            tempContainer.innerHTML = html;
            return tempContainer.offsetHeight;
        }

        renderSections() {
            this.sectionsContainer = document.createElement('div');
            this.sectionsContainer.className = 'viewport-sections-container';

            this.sections.forEach((section, index) => {
                const sectionEl = document.createElement('div');
                sectionEl.className = 'viewport-section';
                sectionEl.dataset.index = index;


                const anchor = this.sectionAnchors[index];
                if (anchor) {
                    sectionEl.id = 'section-' + anchor;
                }

                const contentEl = document.createElement('div');
                contentEl.className = 'viewport-section-content';

                if (Array.isArray(section.elements)) {
                    section.elements.forEach(html => {
                        const wrapper = document.createElement('div');
                        wrapper.innerHTML = html;
                        while (wrapper.firstChild) {
                            contentEl.appendChild(wrapper.firstChild);
                        }
                    });
                } else {
                    contentEl.innerHTML = section.elements;
                }

                if (section.isPartial && section.partNumber < section.totalParts) {
                    const continuesEl = document.createElement('div');
                    continuesEl.className = 'viewport-section-continues';
                    continuesEl.textContent = 'continues';
                    sectionEl.appendChild(continuesEl);
                }

                sectionEl.appendChild(contentEl);

                if (index < this.sections.length - 1) {
                    const divider = document.createElement('div');
                    divider.className = 'viewport-section-divider';
                    sectionEl.appendChild(divider);
                }

                this.sectionsContainer.appendChild(sectionEl);
            });

            this.container.innerHTML = '';
            this.container.appendChild(this.sectionsContainer);
        }

        createNavigation() {
            this.flipper = window.SectionFlipper.createNav(this.sections.length, {
                initial: this.currentIndex,
                ariaLabel: 'Sections',
                onSelect: (index) => {
                    if (!this.isTransitioning) this.goToSection(index);
                }
            });
        }

        updateNavigation() {
            this.flipper.setActive(this.currentIndex);
        }

        setupEventListeners() {
            window.addEventListener('wheel', this.boundHandleWheel, { passive: false });
            window.addEventListener('keydown', this.boundHandleKeydown);
            window.addEventListener('touchstart', this.boundHandleTouchStart, { passive: true });
            window.addEventListener('touchmove', this.boundHandleTouchMove, { passive: false });
            window.addEventListener('hashchange', this.boundHandleHashChange);
        }

        handleWheel(e) {
            if (this.isTransitioning) {
                e.preventDefault();
                return;
            }

            e.preventDefault();

            const delta = e.deltaY;
            this.accumulatedDelta += delta;

            clearTimeout(this.scrollTimeout);
            this.scrollTimeout = setTimeout(() => {
                if (Math.abs(this.accumulatedDelta) >= CONFIG.scrollThreshold) {
                    if (this.accumulatedDelta > 0 && this.currentIndex < this.sections.length - 1) {
                        this.goToSection(this.currentIndex + 1);
                    } else if (this.accumulatedDelta < 0 && this.currentIndex > 0) {
                        this.goToSection(this.currentIndex - 1);
                    }
                }
                this.accumulatedDelta = 0;
            }, 80);
        }

        handleKeydown(e) {
            if (this.isTransitioning) return;

            if (!this.container.closest(':focus-within') && 
                document.activeElement !== document.body) return;

            switch (e.key) {
                case 'ArrowDown':
                case 'PageDown':
                    e.preventDefault();
                    if (this.currentIndex < this.sections.length - 1) {
                        this.goToSection(this.currentIndex + 1);
                    }
                    break;
                case 'ArrowUp':
                case 'PageUp':
                    e.preventDefault();
                    if (this.currentIndex > 0) {
                        this.goToSection(this.currentIndex - 1);
                    }
                    break;
                case ' ':
                    if (!e.shiftKey && this.currentIndex < this.sections.length - 1) {
                        e.preventDefault();
                        this.goToSection(this.currentIndex + 1);
                    }
                    break;
            }
        }

        handleTouchStart(e) {
            this.touchStartY = e.touches[0].clientY;
            this.touchStartTime = Date.now();
        }

        handleTouchMove(e) {
            if (this.isTransitioning) {
                e.preventDefault();
                return;
            }

            const touchEndY = e.touches[0].clientY;
            const delta = this.touchStartY - touchEndY;
            const timeDelta = Date.now() - this.touchStartTime;

            if (Math.abs(delta) > 30 && timeDelta > 50) {
                e.preventDefault();

                if (delta > 0 && this.currentIndex < this.sections.length - 1) {
                    this.goToSection(this.currentIndex + 1);
                } else if (delta < 0 && this.currentIndex > 0) {
                    this.goToSection(this.currentIndex - 1);
                }

                this.touchStartY = touchEndY;
                this.touchStartTime = Date.now();
            }
        }

        showSection(index) {
            const sectionElements = this.sectionsContainer.querySelectorAll('.viewport-section');

            sectionElements.forEach((section, i) => {
                if (i === index) {
                    section.classList.add('active');
                    section.style.display = 'flex';
                    section.style.visibility = 'visible';
                    section.style.opacity = '1';
                } else {
                    section.classList.remove('active');
                    section.style.display = 'none';
                    section.style.visibility = 'hidden';
                    section.style.opacity = '0';
                }
            });
        }

        goToSection(targetIndex) {
            if (this.isTransitioning || targetIndex === this.currentIndex) return;
            if (targetIndex < 0 || targetIndex >= this.sections.length) return;

            const now = Date.now();
            if (now - this.lastScrollTime < CONFIG.scrollCooldown) return;

            this.isTransitioning = true;
            this.lastScrollTime = now;

            const sectionElements = this.sectionsContainer.querySelectorAll('.viewport-section');
            const currentSection = sectionElements[this.currentIndex];
            const nextSection = sectionElements[targetIndex];

            if (window.triggerGlitch) {
                window.triggerGlitch(150);
            }

            currentSection.style.transition = `opacity ${CONFIG.transitionDuration / 2}ms ease-out`;
            currentSection.style.opacity = '0';

            setTimeout(() => {
                currentSection.classList.remove('active');
                currentSection.style.display = 'none';
                currentSection.style.visibility = 'hidden';

                nextSection.style.display = 'flex';
                nextSection.style.visibility = 'visible';
                nextSection.style.opacity = '0';
                nextSection.style.transition = `opacity ${CONFIG.transitionDuration / 2}ms ease-in`;

                nextSection.offsetHeight;

                nextSection.classList.add('active');
                nextSection.style.opacity = '1';

                this.currentIndex = targetIndex;
                this.updateNavigation();
                this.updateHash(targetIndex);

                window.dispatchEvent(new CustomEvent('viewportsectionchange', {
                    detail: { 
                        from: this.currentIndex, 
                        to: targetIndex,
                        totalSections: this.sections.length,
                        anchor: this.sectionAnchors[targetIndex]
                    }
                }));

                setTimeout(() => {
                    this.isTransitioning = false;
                }, CONFIG.transitionDuration / 2);
            }, CONFIG.transitionDuration / 2);
        }

        destroy() {
            window.removeEventListener('wheel', this.boundHandleWheel);
            window.removeEventListener('keydown', this.boundHandleKeydown);
            window.removeEventListener('touchstart', this.boundHandleTouchStart);
            window.removeEventListener('touchmove', this.boundHandleTouchMove);
            window.removeEventListener('hashchange', this.boundHandleHashChange);

            if (this.flipper) this.flipper.destroy();

            this.container.innerHTML = this.originalContent;
        }

        getCurrentIndex() {
            return this.currentIndex;
        }

        getTotalSections() {
            return this.sections.length;
        }

        getCurrentAnchor() {
            return this.sectionAnchors[this.currentIndex] || null;
        }

        getAnchors() {
            return [...this.sectionAnchors];
        }

        goToAnchor(anchor) {
            const index = this.sectionAnchors.findIndex(a => a === anchor.toLowerCase());
            if (index !== -1) {
                this.goToSection(index);
                return true;
            }
            return false;
        }
    }

    function init() {
        const containers = document.querySelectorAll('[data-viewport-sections]');
        containers.forEach(container => {
            const instance = new ViewportSections(container);
            instances.push(instance);
        });
    }

    function destroyAll() {
        instances.forEach(instance => instance.destroy());
        instances = [];
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.addEventListener('resize', () => {
        clearTimeout(window.viewportSectionsResizeTimeout);
        window.viewportSectionsResizeTimeout = setTimeout(() => {
            destroyAll();
            init();
        }, 250);
    });

    window.ViewportSections = {
        init: init,
        destroy: destroyAll,
        getInstance: (container) => instances.find(i => i.container === container),
        getInstances: () => instances
    };
})();
