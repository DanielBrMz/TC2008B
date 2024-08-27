using UnityEngine;
// Trigger behaviour for the sensors
public class SensorTrigger : MonoBehaviour
{
  public Agent parentAgent;
  public char direction;

  private void OnTriggerEnter(Collider other)
  {
    int value = Utils.DetermineColliderType(other.gameObject.layer);

    if (parentAgent != null)
    {
      parentAgent.UpdateSensorValue(direction, value);
    } else 
    {
      Debug.LogError("The parent agent is not set correctly");
    }
  }

  private void OnTriggerExit(Collider other)
  {
    parentAgent.UpdateSensorValue(direction, 0);
  }
}