"""
User interface module for the DeFi Arbitrage Trading System.

This module provides a minimal web-based user interface for monitoring and controlling
the arbitrage trading system.
"""

import logging
import os
import json
import time
from typing import Dict, List, Optional
import threading
import asyncio
from datetime import datetime

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS

from src.config.config import UI_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ui")

# Initialize Flask app
app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(__file__), "static"),
            template_folder=os.path.join(os.path.dirname(__file__), "templates"))
CORS(app)

# Global reference to the arbitrage system
arbitrage_system = None

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get the current system status."""
    if arbitrage_system is None:
        return jsonify({
            "status": "not_running",
            "message": "Arbitrage system not initialized",
            "stats": {}
        })
    
    stats = arbitrage_system.get_system_stats()
    
    return jsonify({
        "status": "running" if arbitrage_system.running else "stopped",
        "auto_execute": arbitrage_system.auto_execute,
        "min_profit_threshold": arbitrage_system.min_profit_threshold,
        "stats": stats
    })

@app.route('/api/opportunities')
def get_opportunities():
    """Get the current arbitrage opportunities."""
    if arbitrage_system is None:
        return jsonify([])
    
    limit = request.args.get('limit', default=10, type=int)
    opportunities = arbitrage_system.get_best_opportunities(limit=limit)
    
    return jsonify(opportunities)

@app.route('/api/simulations')
def get_simulations():
    """Get the profitable simulated trades."""
    if arbitrage_system is None:
        return jsonify([])
    
    limit = request.args.get('limit', default=10, type=int)
    simulations = arbitrage_system.get_profitable_simulations(limit=limit)
    
    return jsonify(simulations)

@app.route('/api/executions')
def get_executions():
    """Get the successful trade executions."""
    if arbitrage_system is None:
        return jsonify([])
    
    limit = request.args.get('limit', default=10, type=int)
    executions = arbitrage_system.get_successful_executions(limit=limit)
    
    return jsonify(executions)

@app.route('/api/execute', methods=['POST'])
def execute_trade():
    """Manually execute a trade."""
    if arbitrage_system is None:
        return jsonify({
            "status": "error",
            "message": "Arbitrage system not initialized"
        })
    
    trade_data = request.json
    if not trade_data:
        return jsonify({
            "status": "error",
            "message": "No trade data provided"
        })
    
    # Execute the trade asynchronously
    def execute_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(arbitrage_system.execute_trade(trade_data))
        loop.close()
        return result
    
    # Start execution in a separate thread
    thread = threading.Thread(target=execute_async)
    thread.start()
    
    return jsonify({
        "status": "pending",
        "message": "Trade execution started",
        "trade_id": trade_data.get("id", "unknown")
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update system settings."""
    if arbitrage_system is None:
        return jsonify({
            "status": "error",
            "message": "Arbitrage system not initialized"
        })
    
    settings = request.json
    if not settings:
        return jsonify({
            "status": "error",
            "message": "No settings provided"
        })
    
    # Update auto-execute setting
    if "auto_execute" in settings:
        auto_execute = settings["auto_execute"]
        arbitrage_system.set_auto_execute(auto_execute)
    
    # Update minimum profit threshold
    if "min_profit_threshold" in settings:
        min_profit_threshold = float(settings["min_profit_threshold"])
        arbitrage_system.set_min_profit_threshold(min_profit_threshold)
    
    return jsonify({
        "status": "success",
        "message": "Settings updated successfully"
    })

@app.route('/api/start', methods=['POST'])
def start_system():
    """Start the arbitrage system."""
    global arbitrage_system
    
    if arbitrage_system is None:
        return jsonify({
            "status": "error",
            "message": "Arbitrage system not initialized"
        })
    
    if arbitrage_system.running:
        return jsonify({
            "status": "warning",
            "message": "System is already running"
        })
    
    # Get auto-execute setting
    auto_execute = request.json.get("auto_execute", False) if request.json else False
    
    # Start the system asynchronously
    def start_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(arbitrage_system.start(auto_execute=auto_execute))
        loop.close()
    
    # Start in a separate thread
    thread = threading.Thread(target=start_async)
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": f"System starting (auto_execute={auto_execute})"
    })

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """Stop the arbitrage system."""
    if arbitrage_system is None:
        return jsonify({
            "status": "error",
            "message": "Arbitrage system not initialized"
        })
    
    if not arbitrage_system.running:
        return jsonify({
            "status": "warning",
            "message": "System is not running"
        })
    
    # Stop the system asynchronously
    def stop_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(arbitrage_system.stop())
        loop.close()
    
    # Stop in a separate thread
    thread = threading.Thread(target=stop_async)
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": "System stopping"
    })

def create_ui_templates():
    """Create the UI templates directory and files."""
    # Create templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create static directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
    
    # Create index.html template
    index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeFi Arbitrage Trading System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 d-none d-md-block bg-light sidebar">
                <div class="sidebar-sticky">
                    <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                        <span>System Control</span>
                    </h6>
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link active" href="#" id="dashboard-link">
                                Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" id="opportunities-link">
                                Opportunities
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" id="simulations-link">
                                Simulations
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" id="executions-link">
                                Executions
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#" id="settings-link">
                                Settings
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>

            <main role="main" class="col-md-10 ml-sm-auto col-lg-10 px-4">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">DeFi Arbitrage Trading System</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <div class="btn-group mr-2">
                            <button type="button" class="btn btn-sm btn-outline-success" id="start-button">Start System</button>
                            <button type="button" class="btn btn-sm btn-outline-danger" id="stop-button">Stop System</button>
                        </div>
                    </div>
                </div>

                <!-- System Status -->
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                System Status
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Status</h5>
                                                <p class="card-text" id="system-status">Not Running</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Auto-Execute</h5>
                                                <p class="card-text" id="auto-execute-status">Disabled</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Runtime</h5>
                                                <p class="card-text" id="runtime">0 hours</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Min Profit</h5>
                                                <p class="card-text" id="min-profit-threshold">0.5%</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Dashboard Content -->
                <div id="dashboard-content" class="content-section">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    Performance Metrics
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card bg-light mb-3">
                                                <div class="card-body">
                                                    <h5 class="card-title">Total Profit</h5>
                                                    <p class="card-text" id="total-profit">$0.00</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card bg-light mb-3">
                                                <div class="card-body">
                                                    <h5 class="card-title">Success Rate</h5>
                                                    <p class="card-text" id="success-rate">0%</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card bg-light mb-3">
                                                <div class="card-body">
                                                    <h5 class="card-title">Trades Executed</h5>
                                                    <p class="card-text" id="trades-executed">0</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card bg-light mb-3">
                                                <div class="card-body">
                                                    <h5 class="card-title">Avg Profit/Trade</h5>
                                                    <p class="card-text" id="avg-profit-per-trade">$0.00</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    System Activity
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card bg-light mb-3">
     
(Content truncated due to size limit. Use line ranges to read in chunks)