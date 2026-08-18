

'use strict';

const TreeView = (function() {
    const CONFIG = {
        lineColor: 'currentColor',
        lineWidth: 1,
        nodeSize: 6,
        indentSize: 24,
        animationDuration: 300
    };

    class TreeViewInstance {
        constructor(container, data, options = {}) {
            this.container = typeof container === 'string' 
                ? document.querySelector(container) 
                : container;

            if (!this.container) {
                console.error('TreeView: Container not found');
                return;
            }

            this.data = data || [];
            this.options = {
                lineColor: options.lineColor || CONFIG.lineColor,
                lineWidth: options.lineWidth || CONFIG.lineWidth,
                nodeSize: options.nodeSize || CONFIG.nodeSize,
                indentSize: options.indentSize || CONFIG.indentSize,
                animationDuration: options.animationDuration || CONFIG.animationDuration,
                onNodeClick: options.onNodeClick || null,
                showIcons: options.showIcons !== false,
                compact: options.compact || false
            };

            this.render();
        }

        render() {
            this.container.innerHTML = '';
            this.container.className = 'tree-view' + (this.options.compact ? ' tree-view-compact' : '');

            const tree = this.buildTree(this.data, 0);
            this.container.appendChild(tree);
        }

        buildTree(items, level) {
            const ul = document.createElement('div');
            ul.className = 'tree-view-level';
            ul.style.paddingLeft = level > 0 ? `${this.options.indentSize}px` : '0';

            items.forEach((item, index) => {
                const isLast = index === items.length - 1;
                const node = this.createNode(item, level, isLast, index);
                ul.appendChild(node);

                if (item.children && item.children.length > 0) {
                    const childTree = this.buildTree(item.children, level + 1);
                    ul.appendChild(childTree);
                }
            });

            return ul;
        }

        createNode(item, level, isLast, index) {
            const node = document.createElement('div');
            node.className = 'tree-view-node';
            node.dataset.level = level;
            node.dataset.index = index;

            const connector = document.createElement('div');
            connector.className = 'tree-view-connector';

            const verticalLine = document.createElement('span');
            verticalLine.className = 'tree-line-vertical';
            if (isLast) verticalLine.classList.add('tree-line-last');

            const horizontalLine = document.createElement('span');
            horizontalLine.className = 'tree-line-horizontal';

            connector.appendChild(verticalLine);
            connector.appendChild(horizontalLine);

            const content = document.createElement('div');
            content.className = 'tree-view-content';

            if (item.icon && this.options.showIcons) {
                const icon = document.createElement('img');
                icon.src = item.icon;
                icon.alt = item.label || '';
                icon.className = 'tree-view-icon';
                content.appendChild(icon);
            }

            const label = document.createElement('span');
            label.className = 'tree-view-label';
            if (item.isBold) label.classList.add('tree-view-label-bold');
            if (item.isSubtle) label.classList.add('tree-view-label-subtle');
            label.textContent = item.label || '';
            content.appendChild(label);

            if (item.subtitle) {
                const subtitle = document.createElement('span');
                subtitle.className = 'tree-view-subtitle';
                subtitle.textContent = item.subtitle;
                content.appendChild(subtitle);
            }

            if (item.href) {
                const link = document.createElement('a');
                link.href = item.href;
                link.className = 'tree-view-link';
                link.appendChild(content);
                node.appendChild(connector);
                node.appendChild(link);
            } else {
                node.appendChild(connector);
                node.appendChild(content);
            }

            if (this.options.onNodeClick && !item.href) {
                content.style.cursor = 'pointer';
                content.addEventListener('click', () => {
                    this.options.onNodeClick(item, node);
                });
            }

            return node;
        }

        update(data) {
            this.data = data;
            this.render();
        }

        destroy() {
            this.container.innerHTML = '';
        }
    }

    function create(container, data, options) {
        return new TreeViewInstance(container, data, options);
    }

    function createArchiveTree(year, items) {
        const grouped = {};

        items.forEach(item => {
            const type = item.type || 'other';
            if (!grouped[type]) {
                grouped[type] = [];
            }
            grouped[type].push(item);
        });

        const treeData = [{
            label: year.toString(),
            isBold: true,
            children: Object.entries(grouped).map(([type, typeItems]) => ({
                icon: `/static/images/entities/${type}.svg`,
                label: '',
                children: typeItems.map(item => ({
                    label: `${item.id} ${item.title}`,
                    href: item.href,
                    subtitle: item.subtitle
                }))
            }))
        }];

        return treeData;
    }

    function createDetailTree(config) {
        const { icon, id, title, artist, description, credits } = config;

        const treeData = [{
            icon: icon,
            label: '',
            children: [
                {
                    label: id,
                    isBold: true,
                    children: [
                        { label: title, isBold: true },
                        { label: artist, isSubtle: true }
                    ]
                },
                {
                    label: '',
                    children: [
                        { label: description, isSubtle: true },
                        { label: credits, isSubtle: true }
                    ]
                }
            ]
        }];

        return treeData;
    }

    return {
        create,
        createArchiveTree,
        createDetailTree,
        CONFIG
    };
})();

window.TreeView = TreeView;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = TreeView;
}
