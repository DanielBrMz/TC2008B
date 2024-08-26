using UnityEngine;
// Trigger behaviour for the sensors
public class SensorTrigger : MonoBehaviour
{
  public Agent parentAgent;
  public int sensorIndex;

  private void OnTriggerEnter(Collider other)
  {
    int value = DetermineColliderType(other.gameObject.layer);
    parentAgent.UpdateSensorValue(sensorIndex, value);
  }

  private void OnTriggerExit(Collider other)
  {
    parentAgent.UpdateSensorValue(sensorIndex, 0);
  }

  private int DetermineColliderType(int layer)
  {
    if (layer == LayerMask.NameToLayer("Agent"))
      return 1; // Another agent
    else if (layer == LayerMask.NameToLayer("Object"))
      return 2; // Object
    else if (layer == LayerMask.NameToLayer("Obstacle"))
      return 3; // Obstacle
    else
      return 0; // Unknown (shouldn't happen due to collision matrix)
  }
}