"""
E2E performance tests.

Tests performance benchmarks and load handling.
"""
import pytest
import asyncio
import time
import statistics
from typing import Dict, Any, List

from tests.e2e.utils.mcp_client import E2EMCPClient


@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Test performance benchmarks and load handling."""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_config, test_data_manager, api_client):
        """Set up test environment."""
        self.test_config = test_config
        self.test_data = test_data_manager
        self.api_client = api_client
    
    async def test_concurrent_image_generation(self, valid_test_image):
        """Test concurrent image generation requests."""
        # Create multiple trial sessions
        session_tasks = [
            self.api_client.start_trial_session()
            for _ in range(self.test_config.concurrent_users)
        ]
        
        session_responses = await asyncio.gather(*session_tasks)
        session_ids = []
        
        for response in session_responses:
            if response.status_code == 200:
                session_ids.append(response.json()["session_id"])
        
        if len(session_ids) < 2:
            pytest.skip("Could not create enough trial sessions for concurrent test")
        
        # Prepare concurrent image generation tasks
        import base64
        image_data = base64.b64decode(valid_test_image)
        
        async def generate_image(session_id, task_id):
            start_time = time.time()
            try:
                response = await self.api_client.stylize_image(
                    image_data=image_data,
                    style_id="van_gogh",
                    session_id=session_id,
                    user_prompt=f"Concurrent test {task_id}"
                )
                end_time = time.time()
                
                return {
                    "task_id": task_id,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "task_id": task_id,
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        concurrent_tasks = [
            generate_image(session_ids[i % len(session_ids)], i)
            for i in range(min(5, len(session_ids)))
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*concurrent_tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_results]
        
        # Performance assertions
        assert len(successful_results) >= 1, "At least one request should succeed"
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            # Performance benchmarks
            assert avg_response_time < self.test_config.max_response_time_seconds, \
                f"Average response time {avg_response_time:.2f}s exceeds limit"
            
            assert max_response_time < self.test_config.max_response_time_seconds * 1.5, \
                f"Max response time {max_response_time:.2f}s too high"
        
        # Test that concurrent requests don't take much longer than sequential
        expected_sequential_time = len(concurrent_tasks) * (max(response_times) if response_times else 10)
        concurrency_efficiency = expected_sequential_time / total_time
        
        assert concurrency_efficiency > 1.5, "Concurrent processing should be more efficient than sequential"
    
    async def test_large_image_upload_performance(self):
        """Test performance with maximum allowed image sizes."""
        trial_response = await self.api_client.start_trial_session()
        if trial_response.status_code != 200:
            pytest.skip("Could not create trial session")
        
        session_id = trial_response.json()["session_id"]
        
        # Test with large image
        large_image_b64 = self.test_data.get_test_images()["large_image"]
        import base64
        large_image_data = base64.b64decode(large_image_b64)
        
        start_time = time.time()
        
        response = await self.api_client.stylize_image(
            image_data=large_image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="Large image performance test"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Large images should still process within reasonable time
        if response.status_code == 200:
            assert response_time < self.test_config.max_response_time_seconds * 2, \
                f"Large image took too long: {response_time:.2f}s"
        else:
            # If rejected, should be due to size limits, not timeout
            assert response.status_code == 400, "Large image should be rejected with 400 if too large"
    
    async def test_multi_style_generation_performance(self, valid_test_image):
        """Test performance of generating 4 styles simultaneously."""
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        import base64
        image_data = base64.b64decode(valid_test_image)
        
        start_time = time.time()
        
        response = await self.api_client.stylize_image(
            image_data=image_data,
            session_id=session_id,
            user_prompt="Multi-style performance test"
            # No style_id = 4 random styles
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("multiple_styles"):
                # Multi-style generation should not take more than 1.5x single style time
                max_multi_style_time = self.test_config.max_response_time_seconds * 1.5
                
                assert response_time < max_multi_style_time, \
                    f"Multi-style generation took too long: {response_time:.2f}s"
                
                # Should generate expected number of images
                assert len(result["images"]) == 4, "Should generate 4 different styles"
                
                # All images should be accessible
                assert all("stylized_image_url" in img for img in result["images"])
    
    async def test_api_endpoint_response_times(self):
        """Test response times of various API endpoints."""
        endpoints_to_test = [
            ("GET", "/health", {}),
            ("GET", "/styles", {}),
            ("POST", "/trial/start", {}),
            ("GET", "/pricing/packages", {})
        ]
        
        response_times = {}
        
        for method, endpoint, data in endpoints_to_test:
            start_time = time.time()
            
            if method == "GET":
                response = await self.api_client.client.get(endpoint)
            elif method == "POST":
                response = await self.api_client.client.post(endpoint, json=data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            response_times[endpoint] = response_time
            
            # Fast endpoints should respond quickly
            if endpoint in ["/health", "/styles", "/pricing/packages"]:
                assert response_time < 5.0, f"{endpoint} too slow: {response_time:.2f}s"
        
        # Log performance metrics
        print("\nAPI Endpoint Response Times:")
        for endpoint, time_taken in response_times.items():
            print(f"  {endpoint}: {time_taken:.3f}s")
    
    async def test_database_performance_under_load(self):
        """Test Firestore performance with high trial session creation rate."""
        # Create many trial sessions rapidly to test database performance
        session_creation_tasks = []
        
        start_time = time.time()
        
        for i in range(10):
            task = self.api_client.start_trial_session()
            session_creation_tasks.append(task)
        
        responses = await asyncio.gather(*session_creation_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Count successful sessions
        successful_sessions = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_sessions += 1
        
        # Database should handle reasonable load
        assert successful_sessions >= 5, "Database should handle concurrent session creation"
        
        # Average time per session should be reasonable
        if successful_sessions > 0:
            avg_time_per_session = total_time / len(session_creation_tasks)
            assert avg_time_per_session < 2.0, f"Database operations too slow: {avg_time_per_session:.2f}s per session"
    
    async def test_memory_and_resource_usage(self, valid_test_image):
        """Test that resource usage remains reasonable under load."""
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        import base64
        image_data = base64.b64decode(valid_test_image)
        
        # Generate multiple images in sequence to test memory usage
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            
            response = await self.api_client.stylize_image(
                image_data=image_data,
                style_id="pixel_art",
                session_id=session_id,
                user_prompt=f"Memory test {i+1}"
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                response_times.append(response_time)
        
        if len(response_times) >= 3:
            # Response times should not degrade significantly over time
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            
            avg_first_half = statistics.mean(first_half)
            avg_second_half = statistics.mean(second_half)
            
            # Later requests shouldn't be more than 50% slower
            degradation_ratio = avg_second_half / avg_first_half
            assert degradation_ratio < 1.5, f"Performance degraded over time: {degradation_ratio:.2f}x"
    
    async def test_mcp_performance_benchmarks(self, valid_test_image):
        """Test MCP interface performance."""
        mcp_client = E2EMCPClient(f"{self.test_config.base_url}/mcp")
        
        try:
            await mcp_client.connect()
            
            # Test MCP tool response times
            trial_result = await mcp_client.start_trial_session()
            session_id = trial_result["session_id"]
            
            # Test single image generation performance
            start_time = time.time()
            
            result = await mcp_client.stylize_image(
                image_base64=valid_test_image,
                style_id="van_gogh",
                user_prompt="MCP performance test",
                session_id=session_id
            )
            
            end_time = time.time()
            mcp_response_time = end_time - start_time
            
            assert "stylized_image_url" in result
            assert mcp_response_time < self.test_config.max_response_time_seconds, \
                f"MCP response too slow: {mcp_response_time:.2f}s"
            
            # Test multiple MCP operations
            operations = [
                ("list_styles", {}),
                ("get_style_details", {"style_id": "van_gogh"}),
                ("check_trial_status", {"session_id": session_id})
            ]
            
            operation_times = {}
            
            for operation_name, args in operations:
                start_time = time.time()
                
                if operation_name == "list_styles":
                    await mcp_client.list_styles()
                elif operation_name == "get_style_details":
                    await mcp_client.get_style_details(args["style_id"])
                elif operation_name == "check_trial_status":
                    await mcp_client.check_trial_status(args["session_id"])
                
                end_time = time.time()
                operation_times[operation_name] = end_time - start_time
            
            # MCP operations should be fast
            for operation, time_taken in operation_times.items():
                assert time_taken < 5.0, f"MCP {operation} too slow: {time_taken:.2f}s"
                
        finally:
            await mcp_client.disconnect()
    
    async def test_throughput_measurement(self, valid_test_image):
        """Measure system throughput under controlled load."""
        # Create multiple sessions for throughput test
        num_sessions = min(3, self.test_config.concurrent_users)
        
        session_tasks = [self.api_client.start_trial_session() for _ in range(num_sessions)]
        session_responses = await asyncio.gather(*session_tasks)
        
        session_ids = [
            resp.json()["session_id"] 
            for resp in session_responses 
            if resp.status_code == 200
        ]
        
        if len(session_ids) < 2:
            pytest.skip("Not enough sessions for throughput test")
        
        import base64
        image_data = base64.b64decode(valid_test_image)
        
        # Measure throughput over time period
        test_duration = 60  # 1 minute test
        start_time = time.time()
        completed_requests = 0
        successful_requests = 0
        
        async def throughput_worker(session_id, worker_id):
            nonlocal completed_requests, successful_requests
            
            while time.time() - start_time < test_duration:
                try:
                    response = await self.api_client.stylize_image(
                        image_data=image_data,
                        style_id="pixel_art",
                        session_id=session_id,
                        user_prompt=f"Throughput test {worker_id}-{completed_requests}"
                    )
                    
                    completed_requests += 1
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    
                    # Small delay to avoid overwhelming
                    await asyncio.sleep(1)
                    
                except Exception:
                    completed_requests += 1
        
        # Run throughput test
        workers = [
            throughput_worker(session_ids[i % len(session_ids)], i)
            for i in range(min(3, len(session_ids)))
        ]
        
        await asyncio.gather(*workers)
        
        actual_duration = time.time() - start_time
        
        # Calculate throughput metrics
        requests_per_second = completed_requests / actual_duration
        success_rate = successful_requests / completed_requests if completed_requests > 0 else 0
        
        print(f"\nThroughput Test Results:")
        print(f"  Duration: {actual_duration:.1f}s")
        print(f"  Total requests: {completed_requests}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Requests per second: {requests_per_second:.2f}")
        
        # Basic throughput assertions
        assert requests_per_second > 0.1, "System should handle some requests per second"
        assert success_rate > 0.5, "Most requests should succeed under normal load"