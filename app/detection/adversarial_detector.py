"""
Adversarial input detection module for identifying malicious or crafted inputs
"""
import re
import math
from typing import Dict, List, Any, Optional
import structlog
from collections import Counter

logger = structlog.get_logger(__name__)

class AdversarialDetector:
    """Detects adversarial inputs designed to manipulate AI systems"""
    
    def __init__(self, threshold: float = 0.2):  # Much lower threshold for better detection
        self.threshold = threshold
        
        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+(?:previous|all|the)\s+(?:instructions|prompts|rules)",
            r"forget\s+(?:everything|all|previous)",
            r"new\s+(?:instructions|task|role|persona)",
            r"act\s+as\s+(?:if|a)",
            r"pretend\s+(?:to\s+be|you\s+are)",
            r"roleplay\s+as",
            r"system\s*:\s*",
            r"user\s*:\s*",
            r"assistant\s*:\s*",
            r"override\s+(?:security|safety|guidelines)",
            r"bypass\s+(?:filter|safety|restriction)",
            r"disregard\s+(?:previous|safety|rules)",
            r"switch\s+to\s+(?:developer|admin|god)\s+mode",
            r"enable\s+(?:developer|debug|admin)\s+mode"
        ]
        
        # Jailbreak attempt indicators
        self.jailbreak_indicators = [
            "DAN", "Do Anything Now", "Developer Mode", "evil mode",
            "unrestricted", "uncensored", "no limitations", "no restrictions",
            "break character", "ignore guidelines", "harmful content",
            "jailbreak", "override safety", "disable filters"
        ]
        
        # Obfuscation techniques
        self.obfuscation_patterns = [
            r"[a-z]\s+[a-z]\s+[a-z]",  # Letter spacing
            r"[^\w\s]{3,}",  # Special character sequences
            r"(\w)\1{4,}",  # Repeated characters
            r"[0-9]{3,}",  # Number sequences used as separators
        ]
        
        # Social engineering indicators
        self.social_engineering_keywords = [
            "urgent", "emergency", "confidential", "secret", "classified",
            "administrator", "sudo", "root", "admin access", "privilege",
            "override", "bypass", "hack", "exploit", "vulnerability"
        ]
        
        # Encoding detection patterns
        self.encoding_patterns = [
            r"\\x[0-9a-fA-F]{2}",  # Hex encoding
            r"\\u[0-9a-fA-F]{4}",  # Unicode encoding
            r"%[0-9a-fA-F]{2}",    # URL encoding
            r"[A-Za-z0-9+/]{20,}={0,2}",  # Base64-like
        ]
    
    def detect_adversarial_input(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect adversarial inputs in text
        
        Args:
            text: Input text to analyze
            context: Additional context for detection
            
        Returns:
            Detection result with adversarial score and details
        """
        try:
            detection_scores = {}
            
            # 1. Prompt injection detection
            injection_score = self._detect_prompt_injection(text)
            detection_scores["prompt_injection"] = injection_score
            
            # 2. Jailbreak attempt detection
            jailbreak_score = self._detect_jailbreak_attempts(text)
            detection_scores["jailbreak"] = jailbreak_score
            
            # 3. Obfuscation detection
            obfuscation_score = self._detect_obfuscation(text)
            detection_scores["obfuscation"] = obfuscation_score
            
            # 4. Social engineering detection
            social_eng_score = self._detect_social_engineering(text)
            detection_scores["social_engineering"] = social_eng_score
            
            # 5. Encoding/payload detection
            encoding_score = self._detect_encoding_attacks(text)
            detection_scores["encoding_attacks"] = encoding_score
            
            # 6. Statistical anomaly detection
            anomaly_score = self._detect_statistical_anomalies(text)
            detection_scores["statistical_anomalies"] = anomaly_score
            
            # Calculate weighted overall score
            weights = {
                "prompt_injection": 0.25,
                "jailbreak": 0.25,
                "obfuscation": 0.15,
                "social_engineering": 0.15,
                "encoding_attacks": 0.1,
                "statistical_anomalies": 0.1
            }
            
            overall_score = sum(score * weights[key] for key, score in detection_scores.items())
            
            # Additional risk factors
            risk_factors = self._identify_risk_factors(text, detection_scores)
            
            result = {
                "risk_type": "adversarial",
                "severity_score": min(overall_score, 1.0),
                "confidence": self._calculate_confidence(detection_scores, text),
                "detected": overall_score > self.threshold,
                "details": {
                    "detection_scores": detection_scores,
                    "risk_factors": risk_factors,
                    "analysis": self._generate_adversarial_analysis(detection_scores, risk_factors)
                }
            }
            
            logger.info("adversarial_detection_completed", 
                       score=overall_score, detected=result["detected"])
            return result
            
        except Exception as e:
            logger.error("adversarial_detection_failed", error=str(e))
            return {
                "risk_type": "adversarial",
                "severity_score": 0.0,
                "confidence": 0.0,
                "detected": False,
                "details": {"error": str(e)}
            }
    
    def _detect_prompt_injection(self, text: str) -> float:
        """Detect prompt injection attempts"""
        text_lower = text.lower()
        injection_score = 0.0
        
        for pattern in self.injection_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                injection_score += 0.3 * len(matches)
        
        # Check for system prompt leakage attempts
        system_keywords = ["system prompt", "initial instructions", "base prompt"]
        for keyword in system_keywords:
            if keyword in text_lower:
                injection_score += 0.4
        
        return min(injection_score, 1.0)
    
    def _detect_jailbreak_attempts(self, text: str) -> float:
        """Detect jailbreak attempts"""
        text_lower = text.lower()
        jailbreak_score = 0.0
        
        for indicator in self.jailbreak_indicators:
            if indicator.lower() in text_lower:
                jailbreak_score += 0.3
        
        # Check for role-playing scenarios designed to bypass restrictions
        roleplay_patterns = [
            r"in\s+this\s+hypothetical",
            r"imagine\s+you\s+are",
            r"pretend\s+we\s+are",
            r"for\s+educational\s+purposes"
        ]
        
        for pattern in roleplay_patterns:
            if re.search(pattern, text_lower):
                jailbreak_score += 0.2
        
        return min(jailbreak_score, 1.0)
    
    def _detect_obfuscation(self, text: str) -> float:
        """Detect text obfuscation techniques"""
        obfuscation_score = 0.0
        
        for pattern in self.obfuscation_patterns:
            matches = re.findall(pattern, text)
            if matches:
                obfuscation_score += 0.2 * len(matches)
        
        # Check for mixed language/script obfuscation
        non_ascii_count = sum(1 for char in text if ord(char) > 127)
        if non_ascii_count > len(text) * 0.1:  # >10% non-ASCII
            obfuscation_score += 0.3
        
        # Check for excessive punctuation/symbols
        symbol_count = sum(1 for char in text if not char.isalnum() and not char.isspace())
        if symbol_count > len(text) * 0.2:  # >20% symbols
            obfuscation_score += 0.2
        
        return min(obfuscation_score, 1.0)
    
    def _detect_social_engineering(self, text: str) -> float:
        """Detect social engineering attempts"""
        text_lower = text.lower()
        social_eng_score = 0.0
        
        for keyword in self.social_engineering_keywords:
            if keyword in text_lower:
                social_eng_score += 0.15
        
        # Check for urgency indicators
        urgency_patterns = [
            r"immediately", r"right\s+now", r"asap", r"quickly",
            r"time\s+sensitive", r"deadline", r"expires?"
        ]
        
        for pattern in urgency_patterns:
            if re.search(pattern, text_lower):
                social_eng_score += 0.1
        
        # Check for authority claims
        authority_patterns = [
            r"i\s+am\s+your\s+(?:creator|developer|administrator)",
            r"this\s+is\s+(?:official|authorized|legitimate)",
            r"by\s+order\s+of"
        ]
        
        for pattern in authority_patterns:
            if re.search(pattern, text_lower):
                social_eng_score += 0.3
        
        return min(social_eng_score, 1.0)
    
    def _detect_encoding_attacks(self, text: str) -> float:
        """Detect encoded payloads or injection attempts"""
        encoding_score = 0.0
        
        for pattern in self.encoding_patterns:
            matches = re.findall(pattern, text)
            if matches:
                encoding_score += 0.2 * len(matches)
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(union|select|insert|delete|drop|update)\s+",
            r"'\s*or\s*'?1'?\s*=\s*'?1",
            r";\s*(drop|delete|truncate)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                encoding_score += 0.4
        
        # Check for script injection
        script_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"eval\s*\(",
            r"document\.",
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                encoding_score += 0.3
        
        return min(encoding_score, 1.0)
    
    def _detect_statistical_anomalies(self, text: str) -> float:
        """Detect statistical anomalies in text"""
        if len(text) < 10:
            return 0.0
        
        anomaly_score = 0.0
        
        # Character frequency analysis
        char_freq = Counter(text.lower())
        
        # Check for unusual character distributions
        if len(char_freq) < len(text) * 0.1:  # Very low character diversity
            anomaly_score += 0.3
        
        # Check for excessive repetition
        most_common_char = char_freq.most_common(1)[0]
        if most_common_char[1] > len(text) * 0.5:  # One character >50%
            anomaly_score += 0.4
        
        # Check entropy
        entropy = self._calculate_entropy(text)
        if entropy < 2.0:  # Very low entropy
            anomaly_score += 0.3
        elif entropy > 7.0:  # Very high entropy (random-like)
            anomaly_score += 0.2
        
        return min(anomaly_score, 1.0)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0
        
        char_freq = Counter(text)
        text_len = len(text)
        
        entropy = 0
        for count in char_freq.values():
            probability = count / text_len
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _identify_risk_factors(self, text: str, scores: Dict[str, float]) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        if scores["prompt_injection"] > 0.3:
            risk_factors.append("Potential prompt injection detected")
        
        if scores["jailbreak"] > 0.3:
            risk_factors.append("Jailbreak attempt indicators found")
        
        if scores["obfuscation"] > 0.4:
            risk_factors.append("Text obfuscation techniques detected")
        
        if scores["social_engineering"] > 0.3:
            risk_factors.append("Social engineering patterns identified")
        
        if scores["encoding_attacks"] > 0.2:
            risk_factors.append("Encoded payloads or injection attempts")
        
        if len(text) > 5000:
            risk_factors.append("Unusually long input (potential resource exhaustion)")
        
        return risk_factors
    
    def _calculate_confidence(self, scores: Dict[str, float], text: str) -> float:
        """Calculate confidence in adversarial detection"""
        # Higher confidence when multiple detection methods agree
        positive_detections = sum(1 for score in scores.values() if score > 0.2)
        
        if positive_detections >= 3:
            return 0.9
        elif positive_detections == 2:
            return 0.8
        elif positive_detections == 1:
            return 0.7
        else:
            return 0.6
    
    def _generate_adversarial_analysis(self, scores: Dict[str, float], 
                                     risk_factors: List[str]) -> str:
        """Generate human-readable adversarial analysis"""
        if not any(score > 0.2 for score in scores.values()):
            return "No significant adversarial patterns detected."
        
        analysis = []
        
        high_scores = [key for key, score in scores.items() if score > 0.5]
        if high_scores:
            analysis.append(f"High-risk categories: {', '.join(high_scores)}")
        
        if risk_factors:
            analysis.append(f"Risk factors: {'; '.join(risk_factors)}")
        
        return "; ".join(analysis)
