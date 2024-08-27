using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ContactTrigger : MonoBehaviour
{  
    public Agent parentAgent;

    private void OnTriggerEnter(Collider other) {
        parentAgent.hasCollided = true;
    }

    private void OnTriggerExit(Collider other) {
        parentAgent.hasCollided = false;
    }
}
