const { createApp } = Vue;
const { ElMessage, ElMessageBox } = ElementPlus;

// Register Element Plus Icons
const IconsVue = ElementPlusIconsVue;

const app = createApp({
    data() {
        return {
            // 基础数据
            agentList: [],
            selectedAgent: null,
            searchKeyword: '',
            
            // 对话框控制
            showCreateDialog: false,
            showToolConfigDialog: false,
            editingAgent: null,
            activeTab: 'basic',
            
            // 表单数据
            agentForm: {
                id: '',
                name: '',
                description: '',
                system_prompt: '',
                user_prompt_template: '{user_input}',
                input_format: [],
                output_format: [],
                tools: [],
                temperature: 0.7,
                max_tokens: 1000,
                status: 'draft'
            },
            
            // 工具配置
            currentTool: {},
            toolConfig: {
                url: '',
                method: 'GET',
                headers: ''
            },
            
            // 聊天相关
            chatMessages: [],
            chatInput: '',
            chatLoading: false,
            inputType: 'string',  // 输入类型：string, object, number, array
            
            // 统计
            totalChats: 0,
            
            // 表单验证规则
            formRules: {
                name: [
                    { required: true, message: '请输入Agent名称', trigger: 'blur' },
                    { min: 1, max: 50, message: '名称长度在1到50个字符', trigger: 'blur' }
                ],
                description: [
                    { max: 500, message: '描述不能超过500个字符', trigger: 'blur' }
                ],
                system_prompt: [
                    { required: true, message: '请输入系统提示词', trigger: 'blur' }
                ]
            },
            
            saving: false
        };
    },
    
    computed: {
        activeAgentCount() {
            return this.agentList.filter(agent => agent.status === 'active').length;
        },
        
        errorAgentCount() {
            return this.agentList.filter(agent => agent.status === 'error').length;
        },
        
        filteredAgents() {
            if (!this.searchKeyword) {
                return this.agentList;
            }
            return this.agentList.filter(agent => 
                agent.name.toLowerCase().includes(this.searchKeyword.toLowerCase()) ||
                agent.description.toLowerCase().includes(this.searchKeyword.toLowerCase())
            );
        }
    },
    
    mounted() {
        this.loadAgents();
    },
    
    methods: {
        // 加载Agent列表
        async loadAgents() {
            try {
                const response = await fetch('/api/agents');
                const data = await response.json();
                this.agentList = data;
            } catch (error) {
                ElMessage.error('加载Agent列表失败: ' + error.message);
            }
        },
        
        // 创建新Agent
        createAgent() {
            // 使用新的编辑器页面
            window.location.href = '/static/agent_editor.html';
        },
        
        // 使用旧的创建方式
        createAgentLegacy() {
            this.editingAgent = null;
            this.resetForm();
            this.showCreateDialog = true;
        },
        
        // 编辑Agent
        async editAgent(agent) {
            // 使用新的编辑器页面
            window.location.href = `/static/agent_editor.html?id=${agent.id}`;
        },
        
        // 使用旧的编辑方式
        async editAgentLegacy(agent) {
            try {
                const response = await fetch(`/api/agents/${agent.id}`);
                const config = await response.json();
                
                this.editingAgent = agent;
                this.agentForm = { ...config };
                this.showCreateDialog = true;
            } catch (error) {
                ElMessage.error('加载Agent配置失败: ' + error.message);
            }
        },
        
        // 保存Agent
        async saveAgent() {
            try {
                // 表单验证
                await this.$refs.agentFormRef.validate();
                
                this.saving = true;
                
                const url = this.editingAgent ? `/api/agents/${this.editingAgent.id}` : '/api/agents';
                const method = this.editingAgent ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.agentForm)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    ElMessage.success(result.message);
                    this.showCreateDialog = false;
                    this.loadAgents();
                } else {
                    ElMessage.error(result.message);
                }
            } catch (error) {
                ElMessage.error('保存失败: ' + error.message);
            } finally {
                this.saving = false;
            }
        },
        
        // 删除Agent
        async deleteAgent(agent) {
            try {
                await ElMessageBox.confirm(
                    `确定要删除Agent "${agent.name}" 吗？`,
                    '确认删除',
                    {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }
                );
                
                const response = await fetch(`/api/agents/${agent.id}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    ElMessage.success(result.message);
                    this.loadAgents();
                } else {
                    ElMessage.error(result.message);
                }
            } catch (error) {
                if (error !== 'cancel') {
                    ElMessage.error('删除失败: ' + error.message);
                }
            }
        },
        
        // 测试Agent
        testAgent(agent) {
            this.selectedAgent = agent;
            this.chatMessages = [];
            this.chatInput = '';
            this.inputType = 'string';
        },
        
        // 发送消息
        async sendMessage() {
            if (!this.chatInput.trim() || this.chatLoading) {
                return;
            }
            
            const rawInput = this.chatInput.trim();
            let processedInput = rawInput;
            let inputData = {};
            
            // 根据输入类型处理输入数据
            try {
                switch (this.inputType) {
                    case 'object':
                        processedInput = JSON.parse(rawInput);
                        inputData = processedInput;
                        break;
                    case 'number':
                        processedInput = parseFloat(rawInput);
                        inputData = { value: processedInput };
                        break;
                    case 'array':
                        processedInput = JSON.parse(rawInput);
                        inputData = { items: processedInput };
                        break;
                    default: // string
                        processedInput = rawInput;
                        inputData = { text: processedInput };
                }
            } catch (error) {
                ElMessage.error(`输入格式错误: ${error.message}`);
                return;
            }
            
            this.chatInput = '';
            this.chatLoading = true;
            
            // 添加用户消息
            this.chatMessages.push({
                role: 'user',
                content: `[${this.inputType}] ${typeof processedInput === 'string' ? processedInput : JSON.stringify(processedInput)}`
            });
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        agent_id: this.selectedAgent.id,
                        user_input: processedInput,
                        input_data: inputData,
                        conversation_history: this.chatMessages.slice(0, -1)
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // 显示响应和输出数据
                    let responseContent = result.response;
                    if (result.output_data && Object.keys(result.output_data).length > 0) {
                        responseContent += `\n\n结构化输出:\n${JSON.stringify(result.output_data, null, 2)}`;
                    }
                    
                    this.chatMessages.push({
                        role: 'assistant',
                        content: responseContent
                    });
                    this.totalChats++;
                } else {
                    this.chatMessages.push({
                        role: 'assistant',
                        content: '抱歉，我遇到了一些问题：' + result.message
                    });
                }
            } catch (error) {
                this.chatMessages.push({
                    role: 'assistant',
                    content: '抱歉，网络连接出现问题，请稍后重试。'
                });
            } finally {
                this.chatLoading = false;
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            }
        },
        
        // 滚动到底部
        scrollToBottom() {
            const chatMessages = this.$refs.chatMessages;
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        },
        
        // 添加参数
        addParameter(type) {
            const param = {
                name: '',
                type: 'string',
                description: '',
                required: true
            };
            
            if (type === 'input') {
                this.agentForm.input_format.push(param);
            } else {
                this.agentForm.output_format.push(param);
            }
        },
        
        // 删除参数
        removeParameter(type, index) {
            if (type === 'input') {
                this.agentForm.input_format.splice(index, 1);
            } else {
                this.agentForm.output_format.splice(index, 1);
            }
        },
        
        // 添加工具
        addTool() {
            this.agentForm.tools.push({
                id: Date.now().toString(),
                name: '',
                description: '',
                type: 'knowledge_base',
                parameters: [],
                config: {}
            });
        },
        
        // 删除工具
        removeTool(index) {
            this.agentForm.tools.splice(index, 1);
        },
        
        // 编辑工具配置
        editToolConfig(tool) {
            this.currentTool = tool;
            this.toolConfig = {
                url: tool.config.url || '',
                method: tool.config.method || 'GET',
                headers: tool.config.headers || ''
            };
            this.showToolConfigDialog = true;
        },
        
        // 保存工具配置
        saveToolConfig() {
            this.currentTool.config = { ...this.toolConfig };
            this.showToolConfigDialog = false;
        },
        
        // 重置表单
        resetForm() {
            this.agentForm = {
                id: '',
                name: '',
                description: '',
                system_prompt: '',
                user_prompt_template: '{user_input}',
                input_format: [],
                output_format: [],
                tools: [],
                temperature: 0.7,
                max_tokens: 1000,
                status: 'draft'
            };
        },
        
        // 获取状态类型
        getStatusType(status) {
            const typeMap = {
                'draft': 'info',
                'active': 'success',
                'inactive': 'warning',
                'error': 'danger'
            };
            return typeMap[status] || 'info';
        },
        
        // 格式化日期
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleString('zh-CN');
        },
        
        // 选择Agent
        selectAgent(agent) {
            this.selectedAgent = agent;
            this.chatMessages = [];
            this.inputType = 'string';
        },
        
        // 跳转到可观测性页面
        goToObservability() {
            window.location.href = '/static/observability.html';
        }
    }
});

// Register all icons globally
for (const [key, component] of Object.entries(IconsVue)) {
    app.component(key, component);
}

app.use(ElementPlus).mount('#app');
