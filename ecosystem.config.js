module.exports = {
  apps: [
    {
      name: 'ytify',
      script: 'main.py',
      interpreter: 'python',
      cwd: __dirname,
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
      env: {
        NODE_ENV: 'production'
      },
      // 日誌設定
      error_file: './logs/error.log',
      out_file: './logs/output.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      // 進程管理
      instances: 1,
      exec_mode: 'fork'
    }
  ]
};
