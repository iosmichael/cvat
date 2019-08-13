/*
* Copyright (C) 2019 Intel Corporation
* SPDX-License-Identifier: MIT
*/

/* global
    require:false
    encodeURIComponent:false
*/

(() => {
    const FormData = require('form-data');
    const {
        ServerError,
    } = require('./exceptions');
    const store = require('store');
    const config = require('./config');

    class ServerProxy {
        constructor() {
            const Axios = require('axios');
            Axios.defaults.withCredentials = true;
            Axios.defaults.xsrfHeaderName = 'X-CSRFTOKEN';
            Axios.defaults.xsrfCookieName = 'csrftoken';

            const token = store.get('token');
            if (token) {
                Axios.defaults.headers.common.Authorization = `Token ${token}`;
            }

            async function about() {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/server/about`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get "about" information from the server',
                        code,
                    );
                }

                return response.data;
            }

            async function share(directory) {
                const { backendAPI } = config;
                directory = encodeURIComponent(directory);

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/server/share?directory=${directory}`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get "share" information from the server',
                        code,
                    );
                }

                return response.data;
            }

            async function exception(exceptionObject) {
                const { backendAPI } = config;

                try {
                    await Axios.post(`${backendAPI}/server/exception`, JSON.stringify(exceptionObject), {
                        proxy: config.proxy,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not send an exception to the server',
                        code,
                    );
                }
            }

            async function formats() {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/server/annotation/formats`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get annotation formats from the server',
                        code,
                    );
                }

                return response.data;
            }

            async function login(username, password) {
                const authenticationData = ([
                    `${encodeURIComponent('username')}=${encodeURIComponent(username)}`,
                    `${encodeURIComponent('password')}=${encodeURIComponent(password)}`,
                ]).join('&').replace(/%20/g, '+');

                let authenticationResponse = null;
                try {
                    authenticationResponse = await Axios.post(
                        `${config.backendAPI}/auth/login`,
                        authenticationData,
                        {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            proxy: config.proxy,
                            // do not redirect to a dashboard,
                            // otherwise we don't get a session id in a response
                            maxRedirects: 0,
                        },
                    );
                } catch (errorData) {
                    if (errorData.response.status === 302) {
                        // Redirection code expected
                        authenticationResponse = errorData.response;
                    } else {
                        const code = errorData.response
                            ? errorData.response.status : errorData.code;
                        throw new ServerError(
                            'Could not login on a server',
                            code,
                        );
                    }
                }

                if (authenticationResponse.headers['set-cookie']) {
                    // Browser itself setup cookie and header is none
                    // In NodeJS we need do it manually
                    const cookies = authenticationResponse.headers['set-cookie'].join(';');
                    Axios.defaults.headers.common.Cookie = cookies;
                }

                const token = authenticationResponse.data.key;
                store.set('token', token);
                Axios.defaults.headers.common.Authorization = `Token ${token}`;
            }

            async function logout() {
                try {
                    await Axios.get(`${config.backendAPI}/auth/logout`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not logout from the server',
                        code,
                    );
                }

                store.remove('token');
                Axios.defaults.headers.common.Authorization = '';
            }

            async function authorized() {
                try {
                    await module.exports.users.getSelf();
                } catch (serverError) {
                    if (serverError.code === 401) {
                        return false;
                    }

                    throw serverError;
                }

                return true;
            }

            async function getTasks(filter = '') {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/tasks?${filter}`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get tasks from a server',
                        code,
                    );
                }

                response.data.results.count = response.data.count;
                return response.data.results;
            }

            async function saveTask(id, taskData) {
                const { backendAPI } = config;

                try {
                    await Axios.patch(`${backendAPI}/tasks/${id}`, JSON.stringify(taskData), {
                        proxy: config.proxy,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not save the task on the server',
                        code,
                    );
                }
            }

            async function deleteTask(id) {
                const { backendAPI } = config;

                try {
                    await Axios.delete(`${backendAPI}/tasks/${id}`);
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not delete the task from the server',
                        code,
                    );
                }
            }

            async function createTask(taskData, files, onUpdate) {
                const { backendAPI } = config;

                async function wait(id) {
                    return new Promise((resolve, reject) => {
                        async function checkStatus() {
                            try {
                                const response = await Axios.get(`${backendAPI}/tasks/${id}/status`);
                                if (['Queued', 'Started'].includes(response.data.state)) {
                                    if (response.data.message !== '') {
                                        onUpdate(response.data.message);
                                    }
                                    setTimeout(checkStatus, 1000);
                                } else if (response.data.state === 'Finished') {
                                    resolve();
                                } else if (response.data.state === 'Failed') {
                                    // If request has been successful, but task hasn't been created
                                    // Then passed data is wrong and we can pass code 400
                                    reject(new ServerError(
                                        'Could not create the task on the server',
                                        400,
                                    ));
                                } else {
                                    // If server has another status, it is unexpected
                                    // Therefore it is server error and we can pass code 500
                                    reject(new ServerError(
                                        `Unknown task state has been received: ${response.data.state}`,
                                        500,
                                    ));
                                }
                            } catch (errorData) {
                                const code = errorData.response
                                    ? errorData.response.status : errorData.code;

                                reject(new ServerError(
                                    'Data uploading error occurred',
                                    code,
                                ));
                            }
                        }

                        setTimeout(checkStatus, 1000);
                    });
                }

                const batchOfFiles = new FormData();
                for (const key in files) {
                    if (Object.prototype.hasOwnProperty.call(files, key)) {
                        for (let i = 0; i < files[key].length; i++) {
                            batchOfFiles.append(`${key}[${i}]`, files[key][i]);
                        }
                    }
                }

                let response = null;

                onUpdate('The task is being created on the server..');
                try {
                    response = await Axios.post(`${backendAPI}/tasks`, JSON.stringify(taskData), {
                        proxy: config.proxy,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not put task to the server',
                        code,
                    );
                }

                onUpdate('The data is being uploaded to the server..');
                try {
                    await Axios.post(`${backendAPI}/tasks/${response.data.id}/data`, batchOfFiles, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    await deleteTask(response.data.id);
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not put data to the server',
                        code,
                    );
                }

                try {
                    await wait(response.data.id);
                } catch (createException) {
                    await deleteTask(response.data.id);
                    throw createException;
                }


                const createdTask = await getTasks(`?id=${response.id}`);
                return createdTask[0];
            }

            async function getJob(jobID) {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/jobs/${jobID}`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get jobs from a server',
                        code,
                    );
                }

                return response.data;
            }

            async function saveJob(id, jobData) {
                const { backendAPI } = config;

                try {
                    await Axios.patch(`${backendAPI}/jobs/${id}`, JSON.stringify(jobData), {
                        proxy: config.proxy,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not save the job on the server',
                        code,
                    );
                }
            }

            async function getUsers() {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/users`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get users from the server',
                        code,
                    );
                }

                return response.data.results;
            }

            async function getSelf() {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/users/self`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        'Could not get user data from the server',
                        code,
                    );
                }

                return response.data;
            }

            async function getData(tid, frame) {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/tasks/${tid}/frames/${frame}`, {
                        proxy: config.proxy,
                        responseType: 'blob',
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        `Could not get frame ${frame} for the task ${tid} from the server`,
                        code,
                    );
                }

                return response.data;
            }

            async function getMeta(tid) {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/tasks/${tid}/frames/meta`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        `Could not get frame meta info for the task ${tid} from the server`,
                        code,
                    );
                }

                return response.data;
            }

            // Session is 'task' or 'job'
            async function getAnnotations(session, id) {
                const { backendAPI } = config;

                let response = null;
                try {
                    response = await Axios.get(`${backendAPI}/${session}s/${id}/annotations`, {
                        proxy: config.proxy,
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        `Could not get annotations for the ${session} ${id} from the server`,
                        code,
                    );
                }

                return response.data;
            }

            // Session is 'task' or 'job'
            async function updateAnnotations(session, id, data, action) {
                const { backendAPI } = config;
                let requestFunc = null;
                let url = null;
                if (action.toUpperCase() === 'PUT') {
                    requestFunc = Axios.put.bind(Axios);
                    url = `${backendAPI}/${session}s/${id}/annotations`;
                } else {
                    requestFunc = Axios.patch.bind(Axios);
                    url = `${backendAPI}/${session}s/${id}/annotations?action=${action}`;
                }

                let response = null;
                try {
                    response = await requestFunc(url, JSON.stringify(data), {
                        proxy: config.proxy,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                } catch (errorData) {
                    const code = errorData.response ? errorData.response.status : errorData.code;
                    throw new ServerError(
                        `Could not updated annotations for the ${session} ${id} on the server`,
                        code,
                    );
                }

                return response.data;
            }

            // Session is 'task' or 'job'
            async function uploadAnnotations(session, id, file, format) {
                const { backendAPI } = config;

                let annotationData = new FormData();
                annotationData.append('annotation_file', file);

                return new Promise((resolve, reject) => {
                    async function request() {
                        try {
                            const response = await Axios
                                .put(`${backendAPI}/${session}s/${id}/annotations?format=${format}`, annotationData, {
                                    proxy: config.proxy,
                                });
                            if (response.status === 202) {
                                annotationData = new FormData();
                                setTimeout(request, 3000);
                            } else {
                                resolve();
                            }
                        } catch (errorData) {
                            const code = errorData.response
                                ? errorData.response.status : errorData.code;
                            const error = new ServerError(
                                `Could not upload annotations for the ${session} ${id}`,
                                code,
                            );
                            reject(error);
                        }
                    }

                    setTimeout(request);
                });
            }

            // Session is 'task' or 'job'
            async function dumpAnnotations(id, name, format) {
                const { backendAPI } = config;
                const filename = name.replace(/\//g, '_');
                let url = `${backendAPI}/tasks/${id}/annotations/${filename}?format=${format}`;

                return new Promise((resolve, reject) => {
                    async function request() {
                        try {
                            const response = await Axios
                                .get(`${url}`, {
                                    proxy: config.proxy,
                                });
                            if (response.status === 202) {
                                setTimeout(request, 3000);
                            } else {
                                url = `${url}&action=download`;
                                resolve(url);
                            }
                        } catch (errorData) {
                            const code = errorData.response
                                ? errorData.response.status : errorData.code;
                            const error = new ServerError(
                                `Could not dump annotations for the task ${id} from the server`,
                                code,
                            );
                            reject(error);
                        }
                    }

                    setTimeout(request);
                });
            }

            Object.defineProperties(this, Object.freeze({
                server: {
                    value: Object.freeze({
                        about,
                        share,
                        formats,
                        exception,
                        login,
                        logout,
                        authorized,
                    }),
                    writable: false,
                },

                tasks: {
                    value: Object.freeze({
                        getTasks,
                        saveTask,
                        createTask,
                        deleteTask,
                    }),
                    writable: false,
                },

                jobs: {
                    value: Object.freeze({
                        getJob,
                        saveJob,
                    }),
                    writable: false,
                },

                users: {
                    value: Object.freeze({
                        getUsers,
                        getSelf,
                    }),
                    writable: false,
                },

                frames: {
                    value: Object.freeze({
                        getData,
                        getMeta,
                    }),
                    writable: false,
                },

                annotations: {
                    value: Object.freeze({
                        updateAnnotations,
                        getAnnotations,
                        dumpAnnotations,
                        uploadAnnotations,
                    }),
                    writable: false,
                },
            }));
        }
    }

    const serverProxy = new ServerProxy();
    module.exports = serverProxy;
})();
