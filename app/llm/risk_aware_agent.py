# Real RiskAwareAgent with actual risk detection
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import structlog
from app.detection.bias_detector import BiasDetector
from app.detection.hallucination_detector import HallucinationDetector
from app.detection.pii_detector import PIIDetector
from app.detection.adversarial_detector import AdversarialDetector
from app.scoring.risk_engine import RiskScoringEngine
from app.core.risk_config import EnhancedRiskConfiguration
from app.mitigation.strategies import MitigationEngine

logger = structlog.get_logger(__name__)

@dataclass
class RiskAnalysisResult:
    input_risks: List[Dict[str, Any]]
    output_risks: List[Dict[str, Any]]
    overall_risk_score: Dict[str, Any]
    mitigations_applied: List[str]
    processing_time: float
    request_id: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AgentResponse:
    final_text: str
    original_llm_response: str
    input_risks: List
    output_risks: List
    overall_risk_score: Dict
    mitigations_applied: List
    processing_time: float
    request_id: str
    timestamp: datetime
    metadata: Dict[str, Any]

class RiskAwareAgent:
    def __init__(self, ollama_client=None, config_file: str = "risk_config.json"):
        self.ollama_client = ollama_client
        
        # Load enhanced configuration
        self.risk_config = EnhancedRiskConfiguration(config_file)
        config = self.risk_config.config
        
        # Initialize real risk detection components with configuration
        self.bias_detector = BiasDetector(threshold=config.bias_threshold)
        self.hallucination_detector = HallucinationDetector(threshold=config.hallucination_threshold)
        self.pii_detector = PIIDetector(threshold=config.pii_threshold)
        self.adversarial_detector = AdversarialDetector(threshold=config.adversarial_threshold)
        self.risk_scorer = RiskScoringEngine()
        self.mitigation_engine = MitigationEngine()
        
        logger.info("RiskAwareAgent initialized with enhanced configuration", 
                   global_sensitivity=config.global_sensitivity,
                   bias_threshold=config.bias_threshold,
                   pii_threshold=config.pii_threshold,
                   adversarial_threshold=config.adversarial_threshold,
                   hallucination_threshold=config.hallucination_threshold)
    
    def update_configuration(self, use_case: str = None, custom_config: Dict[str, Any] = None):
        """Update risk detection configuration"""
        if use_case:
            self.risk_config.optimize_for_use_case(use_case)
            logger.info(f"Configuration optimized for use case: {use_case}")
        
        if custom_config:
            for detector_type, new_threshold in custom_config.items():
                if detector_type.endswith("_threshold"):
                    detector_name = detector_type.replace("_threshold", "")
                    self.risk_config.update_threshold(detector_name, new_threshold)
            logger.info("Custom configuration applied", config=custom_config)
        
        # Reinitialize detectors with new configuration
        config = self.risk_config.config
        self.bias_detector.threshold = config.bias_threshold
        self.hallucination_detector.threshold = config.hallucination_threshold
        self.pii_detector.threshold = config.pii_threshold
        self.adversarial_detector.threshold = config.adversarial_threshold
        
    async def health_check(self):
        return {
            "ollama": True,
            "bias_detector": True,
            "hallucination_detector": True,
            "pii_detector": True,
            "adversarial_detector": True,
            "risk_scorer": True,
            "mitigation_engine": True,
            "overall": True
        }
    
    def analyze_input_risks(self, text: str) -> List[Dict[str, Any]]:
        """Analyze input text for various risk types"""
        risks = []
        
        # Run all detectors with enhanced sensitivity
        try:
            # Bias detection
            bias_result = self.bias_detector.detect_bias(text)
            logger.info("bias_detection_completed", 
                       bias_score=bias_result.get("severity_score", 0.0), 
                       detected=bias_result.get("detected", False))
            
            if bias_result.get("detected", False) or bias_result.get("severity_score", 0.0) > 0.2:
                risks.append({
                    "type": "bias",
                    "severity": bias_result.get("severity_score", 0.0),
                    "confidence": bias_result.get("confidence", 0.0),
                    "details": bias_result
                })
            
            # PII detection
            pii_result = self.pii_detector.detect_pii(text)
            logger.info("pii_detection_completed", 
                       score=pii_result.get("severity_score", 0.0), 
                       detected=pii_result.get("detected", False),
                       pii_types=list(pii_result.get("details", {}).get("detected_pii", {}).keys()))
            
            # More sensitive PII detection - if any PII is found, consider it significant
            pii_detected = pii_result.get("detected", False)
            pii_score = pii_result.get("severity_score", 0.0)
            pii_types_found = pii_result.get("details", {}).get("detected_pii", {})
            
            # If we found any PII types, boost the detection
            if pii_types_found and not pii_detected:
                # Check if any high-risk PII was found
                high_risk_found = any(pii_type in ["ssn", "credit_card", "bank_account", "passport"] 
                                    for pii_type in pii_types_found.keys())
                # Check if multiple PII types were found
                multiple_pii = len(pii_types_found) > 1
                
                if high_risk_found or multiple_pii or pii_score > 0.15:
                    pii_detected = True
                    # Boost the score for reporting
                    pii_score = max(pii_score, 0.4)
            
            if pii_detected or pii_score > 0.15:
                risks.append({
                    "type": "pii",
                    "severity": pii_score,
                    "confidence": pii_result.get("confidence", 0.0),
                    "details": pii_result
                })
            
            # Adversarial detection
            adv_result = self.adversarial_detector.detect_adversarial_input(text)
            logger.info("adversarial_detection_completed", 
                       score=adv_result.get("severity_score", 0.0), 
                       detected=adv_result.get("detected", False))
            
            # More sensitive adversarial detection
            adv_detected = adv_result.get("detected", False)
            adv_score = adv_result.get("severity_score", 0.0)
            
            # Lower threshold for adversarial content due to security implications
            if adv_detected or adv_score > 0.25:
                risks.append({
                    "type": "adversarial",
                    "severity": adv_score,
                    "confidence": adv_result.get("confidence", 0.0),
                    "details": adv_result
                })
                
        except Exception as e:
            logger.error("Error in risk analysis", error=str(e))
            
        return risks
    
    def analyze_output_risks(self, text: str, input_text: str = "") -> List[Dict[str, Any]]:
        """Analyze output text for hallucination and other risks"""
        risks = []
        
        try:
            # Hallucination detection
            hall_result = self.hallucination_detector.detect_hallucination(text, {"input": input_text})
            logger.info("hallucination_detection_completed", 
                       score=hall_result.get("severity_score", 0.0), 
                       detected=hall_result.get("detected", False))
            
            if hall_result.get("detected", False) or hall_result.get("severity_score", 0.0) > 0.3:
                risks.append({
                    "type": "hallucination",
                    "severity": hall_result.get("severity_score", 0.0),
                    "confidence": hall_result.get("confidence", 0.0),
                    "details": hall_result
                })
            
            # Also check output for bias and PII
            bias_result = self.bias_detector.detect_bias(text)
            if bias_result.get("detected", False) or bias_result.get("severity_score", 0.0) > 0.2:
                risks.append({
                    "type": "output_bias",
                    "severity": bias_result.get("severity_score", 0.0),
                    "confidence": bias_result.get("confidence", 0.0),
                    "details": bias_result
                })
            
            pii_result = self.pii_detector.detect_pii(text)
            if pii_result.get("detected", False) or pii_result.get("severity_score", 0.0) > 0.3:
                risks.append({
                    "type": "output_pii",
                    "severity": pii_result.get("severity_score", 0.0),
                    "confidence": pii_result.get("confidence", 0.0),
                    "details": pii_result
                })
                
        except Exception as e:
            logger.error("Error in output risk analysis", error=str(e))
            
        return risks
        
    async def process(self, user_input: str, **kwargs):
        """Process user input with comprehensive risk analysis"""
        import time
        start_time = time.time()
        
        # Analyze input risks
        input_risks = self.analyze_input_risks(user_input)
        
        # Generate LLM response
        if self.ollama_client:
            try:
                response = await self.ollama_client.generate(
                    prompt=user_input,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 500)
                )
                final_text = response.text
            except Exception as e:
                logger.error("Error generating LLM response", error=str(e))
                final_text = "I apologize, but I'm having trouble processing your request right now."
        else:
            final_text = "I'm currently offline. Please make sure the language model is available."
        
        # Analyze output risks
        output_risks = self.analyze_output_risks(final_text, user_input)
        
        # Apply simple but effective mitigation
        mitigated_text = final_text
        mitigations_applied = []
        
        # Check for high-risk content that needs immediate mitigation
        all_risks = input_risks + output_risks
        for risk in all_risks:
            risk_type = risk.get("type", "")
            severity = risk.get("severity", 0)
            
            if severity >= 0.3:  # Medium/High risk threshold
                if "pii" in risk_type.lower():
                    # For PII risks, replace with privacy-safe response
                    mitigated_text = "I understand you've shared some personal information with me. For your privacy and security, I'd prefer not to repeat or store personal details like names, addresses, or other identifying information. Is there something else I can help you with instead?"
                    mitigations_applied.append("pii_privacy_protection")
                    logger.info("Applied PII mitigation", severity=severity, risk_type=risk_type)
                    break  # Exit after first mitigation
                elif "bias" in risk_type.lower():
                    mitigated_text = f"{final_text}\n\n[Note: I strive to provide balanced, unbiased information. Please consider multiple perspectives on complex topics.]"
                    mitigations_applied.append("bias_disclaimer")
                elif "hallucination" in risk_type.lower() and severity > 0.5:
                    mitigated_text = f"I want to be transparent that I'm not entirely certain about this information: {final_text}\n\nPlease verify this information from reliable sources."
                    mitigations_applied.append("hallucination_disclaimer")
        
        # Calculate overall risk score
        if all_risks:
            max_severity = max(risk["severity"] for risk in all_risks)
            avg_confidence = sum(risk["confidence"] for risk in all_risks) / len(all_risks)
            
            if max_severity >= 0.7:
                risk_level = "high"
            elif max_severity >= 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
        else:
            max_severity = 0.1
            avg_confidence = 0.9
            risk_level = "low"
        
        overall_risk_score = {
            "overall_score": max_severity,
            "risk_level": risk_level,
            "confidence": avg_confidence
        }
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            final_text=mitigated_text,  # Use mitigated text instead of original
            original_llm_response=final_text,  # Keep original for comparison
            input_risks=input_risks,
            output_risks=output_risks,
            overall_risk_score=overall_risk_score,
            mitigations_applied=mitigations_applied,  # Include actual mitigations applied
            processing_time=processing_time,
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            metadata={"input_text": user_input}
        )
        
    async def chat(self, messages: List[Dict[str, str]], **kwargs):
        """Chat with comprehensive risk analysis"""
        import time
        start_time = time.time()
        
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Analyze input risks
        input_risks = self.analyze_input_risks(user_message)
        logger.info("Input risk analysis completed", 
                   risks_detected=len(input_risks),
                   user_message_preview=user_message[:50])
        
        # Generate LLM response
        final_text = "I apologize, but I'm having trouble connecting to the language model."
        
        if self.ollama_client:
            try:
                # First check if Ollama is healthy
                is_healthy = self.ollama_client.health_check()
                if not is_healthy:
                    final_text = "I'm currently offline. Please make sure Ollama is running with 'ollama serve' in your terminal."
                else:
                    response = await self.ollama_client.chat(
                        messages=messages,
                        temperature=kwargs.get('temperature', 0.7),
                        max_tokens=kwargs.get('max_tokens', 500)
                    )
                    final_text = response.text if response.text else "I received an empty response. Please try again."
                    
            except Exception as e:
                logger.error("Error generating LLM response", error=str(e))
                final_text = f"I encountered an error: {str(e)}. Please check if Ollama is running and the model is available."
        else:
            final_text = "Ollama client is not initialized. Please check the system configuration."
        
        # Analyze output risks
        output_risks = self.analyze_output_risks(final_text, user_message)
        logger.info("Output risk analysis completed", 
                   risks_detected=len(output_risks))
        
        # Apply simple but effective mitigation
        mitigated_text = final_text
        mitigations_applied = []
        
        # Check for high-risk content that needs immediate mitigation
        all_risks = input_risks + output_risks
        for risk in all_risks:
            risk_type = risk.get("type", "")
            severity = risk.get("severity", 0)
            
            if severity >= 0.3:  # Medium/High risk threshold
                if "pii" in risk_type.lower():
                    # For PII risks, replace with privacy-safe response
                    mitigated_text = "I understand you've shared some personal information with me. For your privacy and security, I'd prefer not to repeat or store personal details like names, addresses, or other identifying information. Is there something else I can help you with instead?"
                    mitigations_applied.append("pii_privacy_protection")
                    logger.info("Applied PII mitigation", severity=severity, risk_type=risk_type)
                    break  # Exit after first mitigation
                elif "bias" in risk_type.lower():
                    mitigated_text = f"{final_text}\n\n[Note: I strive to provide balanced, unbiased information. Please consider multiple perspectives on complex topics.]"
                    mitigations_applied.append("bias_disclaimer")
                elif "hallucination" in risk_type.lower() and severity > 0.5:
                    mitigated_text = f"I want to be transparent that I'm not entirely certain about this information: {final_text}\n\nPlease verify this information from reliable sources."
                    mitigations_applied.append("hallucination_disclaimer")
        
        # Calculate overall risk score
        if all_risks:
            max_severity = max(risk["severity"] for risk in all_risks)
            avg_confidence = sum(risk["confidence"] for risk in all_risks) / len(all_risks)
            
            if max_severity >= 0.7:
                risk_level = "high"
            elif max_severity >= 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
        else:
            max_severity = 0.1
            avg_confidence = 0.9
            risk_level = "low"
        
        overall_risk_score = {
            "overall_score": max_severity,
            "risk_level": risk_level,
            "confidence": avg_confidence
        }
        
        processing_time = time.time() - start_time
        
        logger.info("Risk analysis completed", 
                   overall_score=max_severity,
                   risk_level=risk_level,
                   input_risks=len(input_risks),
                   output_risks=len(output_risks))
            
        return AgentResponse(
            final_text=mitigated_text,  # Use mitigated text
            original_llm_response=final_text,  # Keep original for comparison
            input_risks=input_risks,
            output_risks=output_risks,
            overall_risk_score=overall_risk_score,
            mitigations_applied=mitigations_applied,  # Include actual mitigations
            processing_time=processing_time,
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            metadata={"user_message": user_message}
        )
        
    async def _analyze_input(self, text: str):
        return [], False
