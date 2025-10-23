const { createApp } = Vue;
const { ElMessage, ElMessageBox } = ElementPlus;

const app = createApp({
    data() {
        return {
            agentForm: {
                id: '',
                name: '',
                description: '',
                input: {},
                tools: [],
                system_prompt: {
                    value: '',
                    ref_objects: []
                },
                task_prompt: {
                    value: '',
                    ref_objects: []
                },
                output: {},
                llm: {
                    id: 'llm_' + Date.now(),
                    name: 'deepseek-chat',
                    temperature: 0.7,
                    max_tokens: 1000,
                    api_base: null,
                    api_key: null
                },
                status: 'draft'
            },
            saving: false,
            showJSONPreview: false,
            jsonPreviewContent: '',
            editingAgentId: null
        };
    },

    mounted() {
        // 检查是否是编辑模式
        const urlParams = new URLSearchParams(window.location.search);
        const agentId = urlParams.get('id');
        if (agentId) {
            this.editingAgentId = agentId;
            this.loadAgent(agentId);
        }
    },

    methods: {
        // 加载Agent配置
        async loadAgent(agentId) {
            try {
                const response = await fetch(`/api/agents/${agentId}`);
                const data = await response.json();
                
                // 转换旧格式到新格式
                this.agentForm = this.normalizeAgentData(data);
                
                ElMessage.success('加载Agent配置成功');
            } catch (error) {
                ElMessage.error('加载Agent配置失败: ' + error.message);
            }
        },

        // 规范化Agent数据
        normalizeAgentData(data) {
            const normalized = {
                id: data.id || '',
                name: data.name || '',
                description: data.description || '',
                input: data.input || {},
                tools: data.tools || [],
                system_prompt: data.system_prompt || { value: '', ref_objects: [] },
                task_prompt: data.task_prompt || { value: '', ref_objects: [] },
                output: data.output || {},
                llm: data.llm || {
                    id: 'llm_' + Date.now(),
                    name: 'deepseek-chat',
                    temperature: 0.7,
                    max_tokens: 1000,
                    api_base: null,
                    api_key: null
                },
                status: data.status || 'draft'
            };

            // 确保input和output中的每个参数都有_name字段用于UI显示
            Object.keys(normalized.input).forEach(key => {
                if (!normalized.input[key]._name) {
                    normalized.input[key]._name = key;
                }
            });
            Object.keys(normalized.output).forEach(key => {
                if (!normalized.output[key]._name) {
                    normalized.output[key]._name = key;
                }
            });

            return normalized;
        },

        // 添加输入参数
        addInputParam() {
            const paramName = 'param_' + Date.now();
            this.agentForm.input[paramName] = {
                _name: paramName,
                type: 'String',
                value: null,
                description: '',
                required: false
            };
        },

        // 更新输入参数的key
        updateInputParamKey(oldKey) {
            const param = this.agentForm.input[oldKey];
            const newKey = param._name;
            
            if (newKey && newKey !== oldKey) {
                delete this.agentForm.input[oldKey];
                this.agentForm.input[newKey] = param;
            }
        },

        // 删除输入参数
        removeInputParam(key) {
            delete this.agentForm.input[key];
        },

        // 添加输出参数
        addOutputParam() {
            const paramName = 'output_' + Date.now();
            this.agentForm.output[paramName] = {
                _name: paramName,
                variable_meta_type: 'String',
                variable_type: null,
                variable_desc: '',
                required: true
            };
        },

        // 更新输出参数的key
        updateOutputParamKey(oldKey) {
            const param = this.agentForm.output[oldKey];
            const newKey = param._name;
            
            if (newKey && newKey !== oldKey) {
                delete this.agentForm.output[oldKey];
                this.agentForm.output[newKey] = param;
            }
        },

        // 删除输出参数
        removeOutputParam(key) {
            delete this.agentForm.output[key];
        },

        // 添加工具
        handleAddTool(type) {
            let tool = { type };
            
            switch(type) {
                case 'system_function':
                    tool = {
                        type: 'system_function',
                        name: 'calculator',
                        description: ''
                    };
                    break;
                case 'call_function':
                    tool = {
                        type: 'call_function',
                        name: '',
                        function_type: 'api',
                        description: '',
                        config: {}
                    };
                    break;
                case 'query_objects':
                    tool = {
                        type: 'query_objects',
                        objects: [],
                        description: ''
                    };
                    break;
            }
            
            this.agentForm.tools.push(tool);
        },

        // 删除工具
        removeTool(index) {
            this.agentForm.tools.splice(index, 1);
        },

        // 添加查询对象
        addQueryObject(toolIndex) {
            const tool = this.agentForm.tools[toolIndex];
            if (!tool.objects) {
                tool.objects = [];
            }
            tool.objects.push({
                object_code: '',
                object_description: '',
                fields: []
            });
        },

        // 删除查询对象
        removeQueryObject(toolIndex, objIndex) {
            this.agentForm.tools[toolIndex].objects.splice(objIndex, 1);
        },

        // 添加对象字段
        addObjectField(toolIndex, objIndex) {
            const obj = this.agentForm.tools[toolIndex].objects[objIndex];
            if (!obj.fields) {
                obj.fields = [];
            }
            obj.fields.push({
                field_name: '',
                field_description: ''
            });
        },

        // 删除对象字段
        removeObjectField(toolIndex, objIndex, fieldIndex) {
            this.agentForm.tools[toolIndex].objects[objIndex].fields.splice(fieldIndex, 1);
        },

        // 添加引用对象
        addRefObject(promptType) {
            const refObject = {
                id: Date.now() % 10000,
                type: 'input_type',
                name: '',
                value: null,
                tag: ''
            };
            
            if (promptType === 'system') {
                this.agentForm.system_prompt.ref_objects.push(refObject);
            } else {
                this.agentForm.task_prompt.ref_objects.push(refObject);
            }
        },

        // 删除引用对象
        removeRefObject(promptType, index) {
            if (promptType === 'system') {
                this.agentForm.system_prompt.ref_objects.splice(index, 1);
            } else {
                this.agentForm.task_prompt.ref_objects.splice(index, 1);
            }
        },

        // 预览JSON
        previewJSON() {
            this.jsonPreviewContent = JSON.stringify(this.prepareDataForSave(), null, 2);
            this.showJSONPreview = true;
        },

        // 复制JSON
        async copyJSON() {
            try {
                await navigator.clipboard.writeText(this.jsonPreviewContent);
                ElMessage.success('JSON已复制到剪贴板');
            } catch (error) {
                ElMessage.error('复制失败: ' + error.message);
            }
        },

        // 准备保存的数据
        prepareDataForSave() {
            const data = JSON.parse(JSON.stringify(this.agentForm));
            
            // 清理input和output中的_name字段
            Object.keys(data.input).forEach(key => {
                delete data.input[key]._name;
            });
            Object.keys(data.output).forEach(key => {
                delete data.output[key]._name;
            });

            // 处理工具配置中的config字段（如果是字符串，转为对象）
            data.tools.forEach(tool => {
                if (tool.type === 'call_function' && typeof tool.config === 'string') {
                    try {
                        tool.config = JSON.parse(tool.config);
                    } catch (e) {
                        tool.config = {};
                    }
                }
            });

            return data;
        },

        // 保存Agent
        async saveAgent() {
            // 验证必填项
            if (!this.agentForm.name) {
                ElMessage.error('请输入Agent名称');
                return;
            }
            if (!this.agentForm.description) {
                ElMessage.error('请输入Agent描述');
                return;
            }
            if (!this.agentForm.system_prompt.value) {
                ElMessage.error('请输入系统提示词');
                return;
            }
            if (!this.agentForm.task_prompt.value) {
                ElMessage.error('请输入任务提示词');
                return;
            }
            if (Object.keys(this.agentForm.output).length === 0) {
                ElMessage.error('请至少添加一个输出参数');
                return;
            }
            if (!this.agentForm.llm.name) {
                ElMessage.error('请选择大模型');
                return;
            }

            this.saving = true;

            try {
                const data = this.prepareDataForSave();
                
                const url = this.editingAgentId 
                    ? `/api/agents/${this.editingAgentId}`
                    : '/api/agents';
                const method = this.editingAgentId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    ElMessage.success(result.message);
                    setTimeout(() => {
                        this.goBack();
                    }, 1000);
                } else {
                    ElMessage.error(result.message);
                }
            } catch (error) {
                ElMessage.error('保存失败: ' + error.message);
            } finally {
                this.saving = false;
            }
        },

        // 返回列表
        goBack() {
            window.location.href = '/static/index.html';
        }
    }
});

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

app.use(ElementPlus).mount('#app');
